from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import aiosqlite


@dataclass(slots=True)
class CatalogItem:
    id: int
    content_type: str
    title: str
    description: str
    year: int | None
    genre: str
    file_id: str | None
    media_type: str | None


@dataclass(slots=True)
class Episode:
    id: int
    series_id: int
    episode_number: int
    title: str
    description: str
    file_id: str
    media_type: str


@dataclass(slots=True)
class MandatoryChannel:
    id: int
    channel_id: str
    name: str
    url: str


class Database:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._connection: aiosqlite.Connection | None = None
        self.admin_ids: set[int] = set()

    async def initialize(
        self, legacy_channel: tuple[str, str, str] | None = None
    ) -> None:
        self._connection = await aiosqlite.connect(self.path)
        self._connection.row_factory = aiosqlite.Row
        await self._connection.execute("PRAGMA foreign_keys = ON")
        await self._connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS contents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content_type TEXT NOT NULL CHECK (content_type IN ('movie', 'series', 'anime')),
                title TEXT NOT NULL COLLATE NOCASE,
                description TEXT NOT NULL DEFAULT '',
                year INTEGER,
                genre TEXT NOT NULL DEFAULT '',
                file_id TEXT,
                media_type TEXT CHECK (media_type IN ('video', 'document', 'audio') OR media_type IS NULL),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS episodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                series_id INTEGER NOT NULL REFERENCES contents(id) ON DELETE CASCADE,
                episode_number INTEGER NOT NULL,
                title TEXT NOT NULL COLLATE NOCASE,
                description TEXT NOT NULL DEFAULT '',
                file_id TEXT NOT NULL,
                media_type TEXT NOT NULL CHECK (media_type IN ('video', 'document', 'audio')),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(series_id, episode_number)
            );

            CREATE INDEX IF NOT EXISTS idx_contents_type ON contents(content_type);
            CREATE INDEX IF NOT EXISTS idx_contents_title ON contents(title);
            CREATE INDEX IF NOT EXISTS idx_episodes_series ON episodes(series_id);

            CREATE TABLE IF NOT EXISTS mandatory_channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                url TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS app_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS admins (
                telegram_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS promotions (
                chat_id INTEGER PRIMARY KEY,
                count INTEGER NOT NULL DEFAULT 1,
                last_sent_date TEXT NOT NULL DEFAULT CURRENT_DATE
            );
            """
        )
        await self._connection.commit()

        # Load extra admin IDs from database
        cursor = await self._connection.execute("SELECT telegram_id FROM admins")
        rows = await cursor.fetchall()
        self.admin_ids = {int(row["telegram_id"]) for row in rows}

        if legacy_channel:
            await self._migrate_legacy_channel(legacy_channel)

    async def _migrate_legacy_channel(
        self, legacy_channel: tuple[str, str, str]
    ) -> None:
        migrated_cursor = await self._db().execute(
            "SELECT value FROM app_settings WHERE key = 'legacy_channel_migrated'"
        )
        if await migrated_cursor.fetchone():
            return

        channel_id, name, url = legacy_channel
        await self._db().execute(
            """
            INSERT OR IGNORE INTO mandatory_channels (channel_id, name, url)
            VALUES (?, ?, ?)
            """,
            (channel_id, name, url),
        )
        await self._db().execute(
            """
            INSERT INTO app_settings (key, value)
            VALUES ('legacy_channel_migrated', '1')
            """,
        )
        await self._db().commit()

    def _db(self) -> aiosqlite.Connection:
        if self._connection is None:
            raise RuntimeError("Database has not been initialized.")
        return self._connection

    async def close(self) -> None:
        if self._connection is not None:
            await self._connection.close()
            self._connection = None

    async def upsert_user(
        self, telegram_id: int, username: str | None, first_name: str
    ) -> None:
        await self._db().execute(
            """
            INSERT INTO users (telegram_id, username, first_name)
            VALUES (?, ?, ?)
            ON CONFLICT(telegram_id) DO UPDATE SET
                username = excluded.username,
                first_name = excluded.first_name,
                updated_at = CURRENT_TIMESTAMP
            """,
            (telegram_id, username, first_name),
        )
        await self._db().commit()

    async def add_content(
        self,
        content_type: str,
        title: str,
        description: str,
        year: int | None,
        genre: str,
        file_id: str | None,
        media_type: str | None,
    ) -> int:
        cursor = await self._db().execute(
            """
            INSERT INTO contents
                (content_type, title, description, year, genre, file_id, media_type)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (content_type, title, description, year, genre, file_id, media_type),
        )
        await self._db().commit()
        return int(cursor.lastrowid)

    async def add_episode(
        self,
        series_id: int,
        episode_number: int,
        title: str,
        description: str,
        file_id: str,
        media_type: str,
    ) -> int:
        cursor = await self._db().execute(
            """
            INSERT INTO episodes
                (series_id, episode_number, title, description, file_id, media_type)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (series_id, episode_number, title, description, file_id, media_type),
        )
        await self._db().commit()
        return int(cursor.lastrowid)

    async def list_contents(
        self, content_type: str, limit: int = 8, offset: int = 0
    ) -> tuple[list[CatalogItem], int]:
        cursor = await self._db().execute(
            """
            SELECT id, content_type, title, description, year, genre, file_id, media_type
            FROM contents
            WHERE content_type = ?
            ORDER BY title COLLATE NOCASE
            LIMIT ? OFFSET ?
            """,
            (content_type, limit, offset),
        )
        rows = await cursor.fetchall()
        count_cursor = await self._db().execute(
            "SELECT COUNT(*) AS count FROM contents WHERE content_type = ?",
            (content_type,),
        )
        count_row = await count_cursor.fetchone()
        return [self._content_from_row(row) for row in rows], int(count_row["count"])

    async def list_admin_contents(self, content_type: str) -> list[CatalogItem]:
        cursor = await self._db().execute(
            """
            SELECT id, content_type, title, description, year, genre, file_id, media_type
            FROM contents
            WHERE content_type = ?
            ORDER BY title COLLATE NOCASE
            LIMIT 500
            """,
            (content_type,)
        )
        return [self._content_from_row(row) for row in await cursor.fetchall()]

    async def list_all_series_and_animes(self) -> list[CatalogItem]:
        """Serial va animeni birga qaytaradi — qism qo'shish oqimi uchun."""
        cursor = await self._db().execute(
            """
            SELECT id, content_type, title, description, year, genre, file_id, media_type
            FROM contents
            WHERE content_type IN ('series', 'anime')
            ORDER BY content_type, title COLLATE NOCASE
            LIMIT 500
            """
        )
        return [self._content_from_row(row) for row in await cursor.fetchall()]

    async def get_content(self, content_id: int) -> CatalogItem | None:
        cursor = await self._db().execute(
            """
            SELECT id, content_type, title, description, year, genre, file_id, media_type
            FROM contents WHERE id = ?
            """,
            (content_id,),
        )
        row = await cursor.fetchone()
        return self._content_from_row(row) if row else None

    async def list_episodes(self, series_id: int) -> list[Episode]:
        cursor = await self._db().execute(
            """
            SELECT id, series_id, episode_number, title, description, file_id, media_type
            FROM episodes
            WHERE series_id = ?
            ORDER BY episode_number
            """,
            (series_id,),
        )
        return [self._episode_from_row(row) for row in await cursor.fetchall()]

    async def get_episode(self, episode_id: int) -> Episode | None:
        cursor = await self._db().execute(
            """
            SELECT id, series_id, episode_number, title, description, file_id, media_type
            FROM episodes WHERE id = ?
            """,
            (episode_id,),
        )
        row = await cursor.fetchone()
        return self._episode_from_row(row) if row else None

    async def delete_episode(self, episode_id: int) -> bool:
        cursor = await self._db().execute(
            "DELETE FROM episodes WHERE id = ?", (episode_id,)
        )
        await self._db().commit()
        return cursor.rowcount > 0

    async def delete_content(self, content_id: int) -> bool:
        """Kontentni (va unga tegishli barcha qismlarni) o'chiradi."""
        cursor = await self._db().execute(
            "DELETE FROM contents WHERE id = ?", (content_id,)
        )
        await self._db().commit()
        return cursor.rowcount > 0

    async def search(self, query: str, limit: int = 12) -> list[dict[str, Any]]:
        pattern = f"%{query}%"
        cursor = await self._db().execute(
            """
            SELECT 'content' AS result_type, id, content_type, title, NULL AS episode_number
            FROM contents
            WHERE title LIKE ? OR description LIKE ? OR genre LIKE ?
            UNION ALL
            SELECT 'episode' AS result_type, e.id, 'episode' AS content_type,
                   c.title || ' — ' || e.title AS title, e.episode_number
            FROM episodes e
            JOIN contents c ON c.id = e.series_id
            WHERE e.title LIKE ? OR e.description LIKE ? OR c.title LIKE ?
            ORDER BY title COLLATE NOCASE
            LIMIT ?
            """,
            (pattern, pattern, pattern, pattern, pattern, pattern, limit),
        )
        return [dict(row) for row in await cursor.fetchall()]

    async def stats(self) -> dict[str, int]:
        cursor = await self._db().execute(
            """
            SELECT
                (SELECT COUNT(*) FROM contents WHERE content_type = 'movie') AS movies,
                (SELECT COUNT(*) FROM contents WHERE content_type = 'series') AS series,
                (SELECT COUNT(*) FROM contents WHERE content_type = 'anime') AS anime,
                (SELECT COUNT(*) FROM episodes) AS episodes,
                (SELECT COUNT(*) FROM users) AS users,
                (SELECT COUNT(*) FROM users WHERE date(updated_at) = date('now')) AS active_today,
                (SELECT COUNT(*) FROM users WHERE date(updated_at) >= date('now', '-30 days')) AS active_month
            """
        )
        row = await cursor.fetchone()
        return {key: int(row[key]) for key in row.keys()}

    async def add_mandatory_channel(
        self, channel_id: str, name: str, url: str
    ) -> int:
        cursor = await self._db().execute(
            """
            INSERT INTO mandatory_channels (channel_id, name, url)
            VALUES (?, ?, ?)
            """,
            (channel_id, name, url),
        )
        await self._db().commit()
        return int(cursor.lastrowid)

    async def list_mandatory_channels(self) -> list[MandatoryChannel]:
        cursor = await self._db().execute(
            """
            SELECT id, channel_id, name, url
            FROM mandatory_channels
            ORDER BY name COLLATE NOCASE
            """
        )
        return [
            MandatoryChannel(
                id=int(row["id"]),
                channel_id=str(row["channel_id"]),
                name=str(row["name"]),
                url=str(row["url"]),
            )
            for row in await cursor.fetchall()
        ]

    async def delete_mandatory_channel(self, channel_id: int) -> bool:
        cursor = await self._db().execute(
            "DELETE FROM mandatory_channels WHERE id = ?", (channel_id,)
        )
        await self._db().commit()
        return cursor.rowcount > 0

    async def add_admin(
        self, telegram_id: int, username: str | None, first_name: str
    ) -> None:
        await self._db().execute(
            """
            INSERT OR REPLACE INTO admins (telegram_id, username, first_name)
            VALUES (?, ?, ?)
            """,
            (telegram_id, username, first_name),
        )
        await self._db().commit()
        self.admin_ids.add(telegram_id)

    async def remove_admin(self, telegram_id: int) -> bool:
        cursor = await self._db().execute(
            "DELETE FROM admins WHERE telegram_id = ?", (telegram_id,)
        )
        await self._db().commit()
        if cursor.rowcount > 0:
            self.admin_ids.discard(telegram_id)
            return True
        return False

    async def list_admins(self) -> list[dict[str, Any]]:
        cursor = await self._db().execute(
            """
            SELECT telegram_id, username, first_name, created_at
            FROM admins
            ORDER BY first_name COLLATE NOCASE
            """
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    def is_admin(self, telegram_id: int) -> bool:
        return telegram_id in self.admin_ids

    async def can_send_promotion(self, chat_id: int) -> bool:
        cursor = await self._db().execute(
            "SELECT count, last_sent_date, date('now', 'localtime') as today FROM promotions WHERE chat_id = ?",
            (chat_id,)
        )
        row = await cursor.fetchone()
        if not row:
            return True
        
        if row["count"] >= 6:
            return False
        if row["last_sent_date"] == row["today"]:
            return False
            
        return True

    async def record_promotion(self, chat_id: int) -> None:
        await self._db().execute(
            """
            INSERT INTO promotions (chat_id, count, last_sent_date)
            VALUES (?, 1, date('now', 'localtime'))
            ON CONFLICT(chat_id) DO UPDATE SET
                count = count + 1,
                last_sent_date = date('now', 'localtime')
            """,
            (chat_id,)
        )
        await self._db().commit()



    @staticmethod
    def _content_from_row(row: aiosqlite.Row) -> CatalogItem:
        return CatalogItem(
            id=int(row["id"]),
            content_type=str(row["content_type"]),
            title=str(row["title"]),
            description=str(row["description"] or ""),
            year=int(row["year"]) if row["year"] is not None else None,
            genre=str(row["genre"] or ""),
            file_id=str(row["file_id"]) if row["file_id"] else None,
            media_type=str(row["media_type"]) if row["media_type"] else None,
        )

    @staticmethod
    def _episode_from_row(row: aiosqlite.Row) -> Episode:
        return Episode(
            id=int(row["id"]),
            series_id=int(row["series_id"]),
            episode_number=int(row["episode_number"]),
            title=str(row["title"]),
            description=str(row["description"] or ""),
            file_id=str(row["file_id"]),
            media_type=str(row["media_type"]),
        )