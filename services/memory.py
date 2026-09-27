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


async def get_history(user_id: int) -> list:
    """Возвращает последние MAX_TURNS*2 сообщений в формате [{role, content}]."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT role, content FROM history WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, MAX_TURNS * 2)
        )
        rows = await cursor.fetchall()
        await cursor.close()
    # Разворачиваем — старое в начало
    return [{"role": r[0], "content": r[1]} for r in reversed(rows)]


async def add_message(user_id: int, role: str, content: str) -> None:
    """Сохраняет сообщение в историю."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO history (user_id, role, content) VALUES (?, ?, ?)",
            (user_id, role, content)
        )
        await db.commit()


async def save_profile(user_id: int, **fields) -> None:
    """Сохраняет/обновляет профиль клиента (имя, телефон, бизнес, город)."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO profiles (user_id, name, phone, business, city, source)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                name = COALESCE(excluded.name, profiles.name),
                phone = COALESCE(excluded.phone, profiles.phone),
                business = COALESCE(excluded.business, profiles.business),
                city = COALESCE(excluded.city, profiles.city),
                source = COALESCE(excluded.source, profiles.source),
                updated_at = CURRENT_TIMESTAMP
        """, (
            user_id,
            fields.get("name"),
            fields.get("phone"),
            fields.get("business"),
            fields.get("city"),
            fields.get("source"),
        ))
        await db.commit()


async def get_profile(user_id: int):
    """Возвращает профиль клиента (dict) или None."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT name, phone, business, city FROM profiles WHERE user_id = ?",
            (user_id,)
        )
        row = await cursor.fetchone()
        await cursor.close()
    if not row:
        return None
    return {"name": row[0], "phone": row[1], "business": row[2], "city": row[3]}
