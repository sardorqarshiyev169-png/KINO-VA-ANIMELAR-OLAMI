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


def content_detail_with_delete_keyboard(
    content_type: str,
    content_id: int,
    has_media: bool,
    is_admin: bool = False,
) -> InlineKeyboardMarkup:
    """Kino/anime uchun detail keyboard — admin bo'lsa o'chirish tugmasi ham chiqadi."""
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
    if is_admin:
        rows.append(
            [
                InlineKeyboardButton(
                    text="🗑 O'chirish",
                    callback_data=f"admin:delete_content:{content_id}:{content_type}",
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


def episode_number_keyboard(
    episodes: list[tuple[int, int, str]],
    content_id: int,
    content_type: str = "series",
    is_admin: bool = False,
) -> InlineKeyboardMarkup:
    """
    Qismlarni raqamlar (1, 2, 3...) ko'rinishida chiqaradi.
    Har qatorda 5 ta raqam tugmasi joylashadi.
    Admin bo'lsa, pastda qismni o'chirish tugmasi chiqadi.
    """
    COLS = 5
    number_buttons = [
        InlineKeyboardButton(
            text=str(number),
            callback_data=f"episode:{episode_id}",
        )
        for episode_id, number, _title in episodes
    ]

    rows: list[list[InlineKeyboardButton]] = []
    for i in range(0, len(number_buttons), COLS):
        rows.append(number_buttons[i : i + COLS])

    if is_admin and episodes:
        rows.append(
            [
                InlineKeyboardButton(
                    text="🗑 Qismni o'chirish",
                    callback_data=f"admin:delete_episode_menu:{content_id}:{content_type}",
                ),
                InlineKeyboardButton(
                    text="🗑 Barchasini o'chirish",
                    callback_data=f"admin:delete_content:{content_id}:{content_type}",
                ),
            ]
        )

    rows.extend(
        [
            [InlineKeyboardButton(text="‹ Ro'yxatga qaytish", callback_data=f"category:{content_type}:0")],
            [InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="home")],
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def episode_delete_menu(
    episodes: list[tuple[int, int, str]],
    content_id: int,
    content_type: str,
) -> InlineKeyboardMarkup:
    """O'chirish uchun qismlar ro'yxati — har biri alohida qator."""
    rows = [
        [
            InlineKeyboardButton(
                text=f"🗑 {number}-qism: {title}",
                callback_data=f"admin:delete_episode:{episode_id}:{content_id}:{content_type}",
            )
        ]
        for episode_id, number, title in episodes
    ]
    rows.append(
        [InlineKeyboardButton(text="‹ Bekor qilish", callback_data=f"content:{content_type}:{content_id}")]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def episode_keyboard(episodes: list[tuple[int, int, str]], content_type: str = "series") -> InlineKeyboardMarkup:
    """Eski funksiya — to'g'ridan-to'g'ri nomlar ko'rinishida (backward compatibility)."""
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


def series_and_anime_picker(items: list[tuple[int, str, str]]) -> InlineKeyboardMarkup:
    """
    Serial va animeni birga ko'rsatadi.
    items: [(id, title, content_type), ...]
    """
    emoji = {"series": "📺", "anime": "🍥"}
    rows = [
        [
            InlineKeyboardButton(
                text=f"{emoji.get(ctype, '🎬')} {title}",
                callback_data=f"admin:episode_series:{series_id}",
            )
        ]
        for series_id, title, ctype in items
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


def admin_menu_inline(is_owner: bool = False) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(text="➕ Kino qo'shish", callback_data="admin:action:add_movie"),
            InlineKeyboardButton(text="➕ Serial qo'shish", callback_data="admin:action:add_series"),
        ],
        [
            InlineKeyboardButton(text="➕ Anime qo'shish", callback_data="admin:action:add_anime"),
            InlineKeyboardButton(text="➕ Qism qo'shish", callback_data="admin:action:add_episode"),
        ],
        [
            InlineKeyboardButton(text="📢 Majburiy a'zolik", callback_data="admin:action:mandatory_membership"),
            InlineKeyboardButton(text="📊 Statistika", callback_data="admin:action:stats"),
        ]
    ]
    if is_owner:
        rows.append([
            InlineKeyboardButton(text="👥 Adminlarni boshqarish", callback_data="admin:action:manage_admins")
        ])
    rows.append([
        InlineKeyboardButton(text="❌ Yopish", callback_data="admin:action:close")
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def mandatory_channels_inline() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="➕ Kanal qo'shish", callback_data="admin:channels:add"),
                InlineKeyboardButton(text="📋 Kanallar ro'yxati", callback_data="admin:channels:list"),
            ],
            [
                InlineKeyboardButton(text="🗑 Kanalni o'chirish", callback_data="admin:channels:delete"),
            ],
            [
                InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin:action:back_to_admin"),
            ]
        ]
    )


def admin_manage_inline() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="➕ Admin qo'shish", callback_data="admin:manage:add"),
                InlineKeyboardButton(text="📋 Adminlar ro'yxati", callback_data="admin:manage:list"),
            ],
            [
                InlineKeyboardButton(text="🗑 Adminni o'chirish", callback_data="admin:manage:delete"),
            ],
            [
                InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin:action:back_to_admin"),
            ]
        ]
    )


def admin_delete_menu(items: list[tuple[int, str]]) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=f"🗑 {name}",
                callback_data=f"admin:delete_admin:{telegram_id}",
            )
        ]
        for telegram_id, name in items
    ]
    rows.append([InlineKeyboardButton(text=CANCEL_BUTTON, callback_data="admin:cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)