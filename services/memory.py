import aiosqlite
from config import DB_PATH

MAX_TURNS = 12


async def init_db() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                role TEXT,
                content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS profiles (
                user_id INTEGER PRIMARY KEY,
                name TEXT,
                phone TEXT,
                business TEXT,
                city TEXT,
                source TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()


# === История диалога ===

async def get_history(user_id: int) -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT role, content FROM history WHERE user_id = ? "
            "ORDER BY id DESC LIMIT ?",
            (user_id, MAX_TURNS),
        )
        rows = await cursor.fetchall()
    return [{"role": r, "content": c} for r, c in reversed(rows)]


async def add_message(user_id: int, role: str, content: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO history (user_id, role, content) VALUES (?, ?, ?)",
            (user_id, role, content),
        )
        await db.commit()


async def reset_history(user_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM history WHERE user_id = ?", (user_id,))
        await db.commit()


# === Профиль клиента ===

async def get_profile(user_id: int) -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT name, phone, business, city, source "
            "FROM profiles WHERE user_id = ?",
            (user_id,),
        )
        row = await cursor.fetchone()
    if row:
        return dict(row)
    return {}


async def update_profile(user_id: int, **fields) -> None:
    """Обновляет только те поля, которые переданы."""
    if not fields:
        return
    async with aiosqlite.connect(DB_PATH) as db:
        # Проверяем, есть ли запись
        cursor = await db.execute(
            "SELECT user_id FROM profiles WHERE user_id = ?",
            (user_id,),
        )
        exists = await cursor.fetchone()
        if exists:
            sets = ", ".join(f"{k} = ?" for k in fields)
            values = list(fields.values()) + [user_id]
            await db.execute(
                f"UPDATE profiles SET {sets}, "
                f"updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
                values,
            )
        else:
            keys = ["user_id"] + list(fields.keys())
            placeholders = ", ".join("?" * len(keys))
            values = [user_id] + list(fields.values())
            await db.execute(
                f"INSERT INTO profiles ({', '.join(keys)}) "
                f"VALUES ({placeholders})",
                values,
            )
        await db.commit()
