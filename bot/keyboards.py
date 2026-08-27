from __future__ import annotations

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

MOVIES_BUTTON = "🎬 Kinolar"
SERIES_BUTTON = "📺 Seriallar"
ANIME_BUTTON = "🍥 Animelar"
SEARCH_BUTTON = "🔎 Qidirish"
CANCEL_BUTTON = "❌ Bekor qilish"
ADMIN_PANEL_BUTTON = "⚙️ Admin panel"
ADD_MOVIE_BUTTON = "➕ Kino qo'shish"
ADD_SERIES_BUTTON = "➕ Serial qo'shish"
ADD_ANIME_BUTTON = "➕ Anime qo'shish"
ADD_EPISODE_BUTTON = "➕ Qism qo'shish"
MANDATORY_MEMBERSHIP_BUTTON = "📢 Majburiy a'zolik"
CATALOG_STATS_BUTTON = "📊 Katalog statistikasi"
ADD_CHANNEL_BUTTON = "➕ Kanal qo'shish"
LIST_CHANNELS_BUTTON = "📋 Kanallar ro'yxati"
DELETE_CHANNEL_BUTTON = "🗑 Kanalni o'chirish"
BACK_ADMIN_BUTTON = "⬅️ Admin panelga qaytish"


def user_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=MOVIES_BUTTON), KeyboardButton(text=SERIES_BUTTON)],
            [KeyboardButton(text=ANIME_BUTTON), KeyboardButton(text=SEARCH_BUTTON)],
        ],
        resize_keyboard=True,
        input_field_placeholder="Bo'limni tanlang",
    )


def admin_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=ADMIN_PANEL_BUTTON)],
            [KeyboardButton(text=ADD_MOVIE_BUTTON), KeyboardButton(text=ADD_SERIES_BUTTON)],
            [KeyboardButton(text=ADD_ANIME_BUTTON), KeyboardButton(text=ADD_EPISODE_BUTTON)],
            [KeyboardButton(text=MANDATORY_MEMBERSHIP_BUTTON)],
            [KeyboardButton(text=CATALOG_STATS_BUTTON), KeyboardButton(text=CANCEL_BUTTON)],
        ],
        resize_keyboard=True,
        input_field_placeholder="Admin amalini tanlang",
    )


def mandatory_channels_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=ADD_CHANNEL_BUTTON)],
            [KeyboardButton(text=LIST_CHANNELS_BUTTON), KeyboardButton(text=DELETE_CHANNEL_BUTTON)],
            [KeyboardButton(text=BACK_ADMIN_BUTTON)],
        ],
        resize_keyboard=True,
        input_field_placeholder="Majburiy a'zolik amalini tanlang",
    )


def subscription_menu(channels: list[tuple[str, str]]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📢 Kanalga qo'shilish",
                    url=channel_url,
                )
            ]
            for _, channel_url in channels
        ]
        + [
            [
                InlineKeyboardButton(
                    text="✅ Tekshirish", callback_data="check_subscription"
                )
            ]
        ]
    )


def pagination_keyboard(
    items: list[tuple[str, str]],
    content_type: str,
    page: int,
    has_next: bool,
) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=title, callback_data=f"content:{content_type}:{item_id}")]
        for title, item_id in items
    ]
    navigation: list[InlineKeyboardButton] = []
    if page > 0:
        navigation.append(
            InlineKeyboardButton(text="‹ Oldingi", callback_data=f"category:{content_type}:{page - 1}")
        )
    if has_next:
        navigation.append(
            InlineKeyboardButton(text="Keyingi ›", callback_data=f"category:{content_type}:{page + 1}")
        )
    if navigation:
        rows.append(navigation)
    rows.append([InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="home")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def content_detail_keyboard(
    content_type: str, content_id: int, has_media: bool
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    if has_media:
        rows.append(
            [
                InlineKeyboardButton(
                    text="▶️ Ko'rish",
                    callback_data=f"send_content:{content_type}:{content_id}",
                )
            ]
        )
    rows.extend(
        [
            [InlineKeyboardButton(text="‹ Ro'yxatga qaytish", callback_data=f"category:{content_type}:0")],
            [InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="home")],
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def episode_keyboard(episodes: list[tuple[int, int, str]], content_type: str = "series") -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=f"{number}-qism: {title}",
                callback_data=f"episode:{episode_id}",
            )
        ]
        for episode_id, number, title in episodes
    ]
    rows.extend(
        [
            [InlineKeyboardButton(text="‹ Ro'yxatga qaytish", callback_data=f"category:{content_type}:0")],
            [InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="home")],
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def episode_content_type_picker() -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(text="📺 Seriallar", callback_data="admin:ep_type:series"),
            InlineKeyboardButton(text="🍥 Animelar", callback_data="admin:ep_type:anime"),
        ],
        [InlineKeyboardButton(text=CANCEL_BUTTON, callback_data="admin:cancel")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def series_picker(items: list[tuple[int, str]]) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=title, callback_data=f"admin:episode_series:{series_id}")]
        for series_id, title in items
    ]
    rows.append([InlineKeyboardButton(text=CANCEL_BUTTON, callback_data="admin:cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def channel_delete_menu(items: list[tuple[int, str]]) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=f"🗑 {name}",
                callback_data=f"admin:delete_channel:{channel_id}",
            )
        ]
        for channel_id, name in items
    ]
    rows.append([InlineKeyboardButton(text=CANCEL_BUTTON, callback_data="admin:cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)