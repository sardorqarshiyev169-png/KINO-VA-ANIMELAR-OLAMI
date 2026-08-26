import aiosqlite
from config import DB_NAME


async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                joined_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS movies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE,
                file_id TEXT,
                title TEXT,
                added_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS animes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE,
                file_id TEXT,
                title TEXT,
                added_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id TEXT,
                username TEXT,
                title TEXT
            )
        """)
        await db.commit()


# ---------- USERS ----------

async def add_user(user_id: int, username: str, full_name: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, username, full_name) VALUES (?, ?, ?)",
            (user_id, username, full_name),
        )
        await db.commit()


async def get_users_count() -> int:
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM users")
        row = await cursor.fetchone()
        return row[0] if row else 0


async def get_all_user_ids() -> list[int]:
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT user_id FROM users")
        rows = await cursor.fetchall()
        return [r[0] for r in rows]


# ---------- MOVIES ----------

async def add_movie(code: str, file_id: str, title: str) -> bool:
    async with aiosqlite.connect(DB_NAME) as db:
        try:
            await db.execute(
                "INSERT INTO movies (code, file_id, title) VALUES (?, ?, ?)",
                (code, file_id, title),
            )
            await db.commit()
            return True
        except aiosqlite.IntegrityError:
            return False


async def get_movie_by_code(code: str):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT file_id, title FROM movies WHERE code = ?", (code,)
        )
        return await cursor.fetchone()


async def delete_movie(code: str) -> bool:
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("DELETE FROM movies WHERE code = ?", (code,))
        await db.commit()
        return cursor.rowcount > 0


async def count_movies() -> int:
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM movies")
        row = await cursor.fetchone()
        return row[0] if row else 0


# ---------- ANIMES ----------

async def add_anime(code: str, file_id: str, title: str) -> bool:
    async with aiosqlite.connect(DB_NAME) as db:
        try:
            await db.execute(
                "INSERT INTO animes (code, file_id, title) VALUES (?, ?, ?)",
                (code, file_id, title),
            )
            await db.commit()
            return True
        except aiosqlite.IntegrityError:
            return False


async def get_anime_by_code(code: str):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT file_id, title FROM animes WHERE code = ?", (code,)
        )
        return await cursor.fetchone()


async def delete_anime(code: str) -> bool:
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("DELETE FROM animes WHERE code = ?", (code,))
        await db.commit()
        return cursor.rowcount > 0


async def count_animes() -> int:
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM animes")
        row = await cursor.fetchone()
        return row[0] if row else 0


# ---------- CHANNELS (majburiy obuna) ----------

async def add_channel(chat_id: str, username: str, title: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT INTO channels (chat_id, username, title) VALUES (?, ?, ?)",
            (chat_id, username, title),
        )
        await db.commit()


async def get_channels():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT id, chat_id, username, title FROM channels")
        return await cursor.fetchall()


async def delete_channel(channel_db_id: int) -> bool:
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("DELETE FROM channels WHERE id = ?", (channel_db_id,))
        await db.commit()
        return cursor.rowcount > 0
