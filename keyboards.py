from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)


def main_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎬 Kino"), KeyboardButton(text="🎭 Anime")],
        ],
        resize_keyboard=True,
    )


def subscription_kb(channels) -> InlineKeyboardMarkup:
    buttons = []
    for ch in channels:
        _, chat_id, username, title = ch
        if username:
            url = f"https://t.me/{username.lstrip('@')}"
        else:
            url = f"https://t.me/c/{str(chat_id).replace('-100', '')}"
        buttons.append([InlineKeyboardButton(text=f"➕ {title or username}", url=url)])
    buttons.append([InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_sub")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_panel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="➕ Kino qo'shish", callback_data="admin_add_movie"),
                InlineKeyboardButton(text="➕ Anime qo'shish", callback_data="admin_add_anime"),
            ],
            [
                InlineKeyboardButton(text="🗑 Kino o'chirish", callback_data="admin_del_movie"),
                InlineKeyboardButton(text="🗑 Anime o'chirish", callback_data="admin_del_anime"),
            ],
            [InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stats")],
            [InlineKeyboardButton(text="📢 Xabar yuborish", callback_data="admin_broadcast")],
            [InlineKeyboardButton(text="📡 Majburiy kanallar", callback_data="admin_channels")],
        ]
    )


def channels_manage_kb(channels) -> InlineKeyboardMarkup:
    buttons = []
    for ch in channels:
        db_id, chat_id, username, title = ch
        buttons.append(
            [InlineKeyboardButton(
                text=f"❌ {title or username}",
                callback_data=f"del_channel_{db_id}",
            )]
        )
    buttons.append([InlineKeyboardButton(text="➕ Kanal qo'shish", callback_data="add_channel")])
    buttons.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin_back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def back_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin_back")]]
    )
