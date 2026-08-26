# Kino Catalog Telegram Bot

A Telegram bot for movies, TV series, and anime built with Python, aiogram 3, and SQLite.

## Features

- Mandatory channel subscription check before users can access the catalog.
- User menu for movies, TV series, anime, and search.
- Inline catalog browsing with pagination.
- Movie and anime delivery by Telegram `file_id`.
- TV series with episode lists and episode delivery by `file_id`.
- Admin-only Telegram panel for adding movies, series, anime, and episodes.
- SQLite persistence with foreign keys and duplicate episode protection.

## Configuration

The bot reads these environment variables:

| Variable | Purpose |
| --- | --- |
| `BOT_TOKEN` | Telegram BotFather token; store it as a secret |
| `ADMIN_ID` | Numeric Telegram user ID allowed to use `/admin` |
| `REQUIRED_CHANNEL_ID` | `@channel_username` or numeric channel ID |
| `REQUIRED_CHANNEL_URL` | Link shown on the subscription button |
| `DATABASE_PATH` | Optional SQLite path; defaults to `data/movies.sqlite3` |

The required values are already configured for this project. Keep the bot added
as an administrator in the required channel so Telegram can verify membership.

## Run

```bash
python main.py
```

The admin opens `/admin`, chooses a content type, and follows the prompts.
For each media item, provide its Telegram file ID and one of `video`,
`document`, or `audio` as the media type.