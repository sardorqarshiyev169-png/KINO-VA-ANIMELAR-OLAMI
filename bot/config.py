from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(
            f"Required environment variable {name} is missing. "
            "Add it to Replit Secrets or environment variables."
        )
    return value


def _admin_id() -> int:
    raw_value = _required("ADMIN_ID")
    try:
        return int(raw_value)
    except ValueError as error:
        raise RuntimeError("ADMIN_ID must be a numeric Telegram user ID.") from error


def _normalise_channel_id(value: str) -> str:
    if value.startswith("https://t.me/"):
        username = value.removeprefix("https://t.me/").split("/", 1)[0]
        return f"@{username}" if not username.startswith("@") else username
    return value


@dataclass(frozen=True, slots=True)
class Settings:
    bot_token: str
    admin_id: int
    required_channel_id: str
    required_channel_url: str
    database_path: Path

    @classmethod
    def from_env(cls) -> "Settings":
        database_path = Path(
            os.getenv("DATABASE_PATH", "data/movies.sqlite3").strip()
            or "data/movies.sqlite3"
        )
        database_path.parent.mkdir(parents=True, exist_ok=True)

        channel_id = _required("REQUIRED_CHANNEL_ID")
        channel_url = _required("REQUIRED_CHANNEL_URL")
        return cls(
            bot_token=_required("BOT_TOKEN"),
            admin_id=_admin_id(),
            required_channel_id=_normalise_channel_id(channel_id),
            required_channel_url=channel_url,
            database_path=database_path,
        )