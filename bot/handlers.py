from __future__ import annotations

import logging
import sqlite3
from typing import Any

from aiogram import Bot, Dispatcher, F, Router
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from bot.config import Settings
from bot.database import CatalogItem, Database
from bot.keyboards import (
    ADD_ANIME_BUTTON,
    ADD_CHANNEL_BUTTON,
    ADD_EPISODE_BUTTON,
    ADD_MOVIE_BUTTON,
    ADD_SERIES_BUTTON,
    ADMIN_PANEL_BUTTON,
    ANIME_BUTTON,
    BACK_ADMIN_BUTTON,
    CATALOG_STATS_BUTTON,
    CANCEL_BUTTON,
    DELETE_CHANNEL_BUTTON,
    LIST_CHANNELS_BUTTON,
    MANDATORY_MEMBERSHIP_BUTTON,
    MOVIES_BUTTON,
    SEARCH_BUTTON,
    SERIES_BUTTON,
    admin_menu,
    content_detail_keyboard,
    channel_delete_menu,
    episode_keyboard,
    mandatory_channels_menu,
    pagination_keyboard,
    series_picker,
    subscription_menu,
    user_menu,
)
from bot.states import ChannelForm, ContentForm, EpisodeForm, SearchForm

logger = logging.getLogger(__name__)


def register_routers(
    dispatcher: Dispatcher, database: Database, settings: Settings
) -> None:
    admin_router = Router(name="admin")
    user_router = Router(name="users")
    register_admin_handlers(admin_router, database, settings)
    register_user_handlers(user_router, database, settings)
    dispatcher.include_router(admin_router)
    dispatcher.include_router(user_router)


def is_admin(user_id: int | None, settings: Settings) -> bool:
    return user_id == settings.admin_id


async def ensure_subscribed(
    event: Message | CallbackQuery,
    bot: Bot,
    database: Database,
    settings: Settings,
) -> bool:
    user = event.from_user
    if user is None or is_admin(user.id, settings):
        return True

    channels = await database.list_mandatory_channels()
    missing_channels = []
    for channel in channels:
        try:
            member = await bot.get_chat_member(
                chat_id=channel.channel_id,
                user_id=user.id,
            )
            subscribed = member.status in {
                ChatMemberStatus.CREATOR,
                ChatMemberStatus.ADMINISTRATOR,
                ChatMemberStatus.MEMBER,
                ChatMemberStatus.RESTRICTED,
            }
        except (TelegramBadRequest, TelegramForbiddenError):
            logger.warning(
                "Could not verify subscription for user %s in %s",
                user.id,
                channel.channel_id,
            )
            subscribed = False
        if not subscribed:
            missing_channels.append(channel)

    if not missing_channels:
        return True

    channel_names = "\n".join(
        f"• <b>{escape_html(channel.name)}</b>" for channel in missing_channels
    )
    text = (
        "🔒 <b>Majburiy a'zolik</b>\n\n"
        "Botdan foydalanish uchun quyidagi kanallarga a'zo bo'ling:\n"
        f"{channel_names}\n\n"
        "A'zo bo'lgach, «✅ Tekshirish» tugmasini bosing."
    )
    if isinstance(event, CallbackQuery):
        await event.answer("Avval barcha kanallarga a'zo bo'ling.", show_alert=True)
        if event.message:
            await event.message.answer(
                text,
                reply_markup=subscription_menu(
                    [(channel.name, channel.url) for channel in missing_channels]
                ),
            )
    else:
        await event.answer(
            text,
            reply_markup=subscription_menu(
                [(channel.name, channel.url) for channel in missing_channels]
            ),
        )
    return False


async def safe_answer(callback: CallbackQuery) -> None:
    try:
        await callback.answer()
    except TelegramBadRequest:
        pass


async def show_home(message: Message, database: Database) -> None:
    await database.upsert_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )
    await message.answer(
        "🎞 <b>Kino katalogiga xush kelibsiz!</b>\n\n"
        "Tomosha qilish uchun bo'limni tanlang:",
        reply_markup=user_menu(),
    )


def register_user_handlers(
    router: Router, database: Database, settings: Settings
) -> None:
    @router.message(Command("start"))
    async def start_handler(message: Message, bot: Bot) -> None:
        if not await ensure_subscribed(message, bot, database, settings):
            return
        await show_home(message, database)

    @router.message(F.text == CANCEL_BUTTON)
    async def user_cancel_handler(
        message: Message, bot: Bot, state: FSMContext
    ) -> None:
        await state.clear()
        if not await ensure_subscribed(message, bot, database, settings):
            return
        await message.answer("Qidirish bekor qilindi.", reply_markup=user_menu())

    @router.callback_query(F.data == "check_subscription")
    async def check_subscription_handler(callback: CallbackQuery, bot: Bot) -> None:
        if not await ensure_subscribed(callback, bot, database, settings):
            return
        await safe_answer(callback)
        if callback.message:
            await callback.message.answer(
                "✅ A'zolik tasdiqlandi. Katalogga xush kelibsiz!",
                reply_markup=user_menu(),
            )

    @router.callback_query(F.data == "home")
    async def home_callback(callback: CallbackQuery, bot: Bot) -> None:
        if not await ensure_subscribed(callback, bot, database, settings):
            return
        await safe_answer(callback)
        if callback.message:
            await callback.message.answer("Bo'limni tanlang:", reply_markup=user_menu())

    @router.message(F.text.in_({MOVIES_BUTTON, SERIES_BUTTON, ANIME_BUTTON}))
    async def category_message(message: Message, bot: Bot) -> None:
        if not await ensure_subscribed(message, bot, database, settings):
            return
        category_map = {
            MOVIES_BUTTON: "movie",
            SERIES_BUTTON: "series",
            ANIME_BUTTON: "anime",
        }
        await send_category(message, database, category_map[message.text], 0)

    @router.callback_query(F.data.startswith("category:"))
    async def category_callback(callback: CallbackQuery, bot: Bot) -> None:
        if not await ensure_subscribed(callback, bot, database, settings):
            return
        await safe_answer(callback)
        if not callback.message:
            return
        _, content_type, page_value = callback.data.split(":")
        await edit_category(
            callback.message,
            database,
            content_type,
            int(page_value),
        )

    @router.callback_query(F.data.startswith("content:"))
    async def content_callback(callback: CallbackQuery, bot: Bot) -> None:
        if not await ensure_subscribed(callback, bot, database, settings):
            return
        await safe_answer(callback)
        if not callback.message:
            return
        _, content_type, content_id_value = callback.data.split(":")
        content = await database.get_content(int(content_id_value))
        if not content:
            await callback.message.answer("Bu ma'lumot endi mavjud emas.")
            return
        await show_content(callback.message, database, content)

    @router.callback_query(F.data.startswith("send_content:"))
    async def send_content_callback(callback: CallbackQuery, bot: Bot) -> None:
        if not await ensure_subscribed(callback, bot, database, settings):
            return
        await safe_answer(callback)
        if not callback.message:
            return
        _, content_type, content_id_value = callback.data.split(":")
        content = await database.get_content(int(content_id_value))
        if not content or not content.file_id or not content.media_type:
            await callback.message.answer("Bu nom uchun fayl hali mavjud emas.")
            return
        await send_media(
            bot,
            callback.from_user.id,
            content.file_id,
            content.media_type,
            f"🎬 <b>{content.title}</b>",
        )

    @router.callback_query(F.data.startswith("episode:"))
    async def episode_callback(callback: CallbackQuery, bot: Bot) -> None:
        if not await ensure_subscribed(callback, bot, database, settings):
            return
        await safe_answer(callback)
        if not callback.message:
            return
        episode_id = int(callback.data.split(":")[1])
        episode = await database.get_episode(episode_id)
        if not episode:
            await callback.message.answer("Bu qism endi mavjud emas.")
            return
        await send_media(
            bot,
            callback.from_user.id,
            episode.file_id,
            episode.media_type,
            f"📺 <b>{episode.title}</b>\n{episode.episode_number}-qism",
        )

    @router.message(F.text == SEARCH_BUTTON)
    async def search_start(message: Message, bot: Bot, state: FSMContext) -> None:
        if not await ensure_subscribed(message, bot, database, settings):
            return
        await state.set_state(SearchForm.query)
        await message.answer(
            "🔎 Katalogdan izlash uchun nom, janr yoki kalit so'z yuboring.\n"
            f"To'xtatish uchun {CANCEL_BUTTON} tugmasini bosing.",
            reply_markup=cancel_keyboard(),
        )

    @router.message(SearchForm.query)
    async def search_query(message: Message, bot: Bot, state: FSMContext) -> None:
        if not await ensure_subscribed(message, bot, database, settings):
            return
        query = (message.text or "").strip()
        if len(query) < 2:
            await message.answer("Kamida ikki belgidan iborat so'z yuboring.")
            return
        results = await database.search(query)
        await state.clear()
        if not results:
            await message.answer(
                f"\"<b>{escape_html(query)}</b>\" bo'yicha natija topilmadi.",
                reply_markup=user_menu(),
            )
            return
        rows: list[list[Any]] = []
        for result in results:
            if result["result_type"] == "content":
                callback_data = f"content:{result['content_type']}:{result['id']}"
            else:
                callback_data = f"episode:{result['id']}"
            rows.append([InlineKeyboardButton(text=result["title"], callback_data=callback_data)])
        await message.answer(
            f"🔎 Results for <b>{escape_html(query)}</b>:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
        )


async def send_category(
    message: Message, database: Database, content_type: str, page: int
) -> None:
    items, total = await database.list_contents(content_type, offset=page * 8)
    label = {"movie": "Kinolar", "series": "Seriallar", "anime": "Animelar"}[content_type]
    if not items:
        await message.answer(
            f"📭 <b>{label}</b>\n\nKatalog hozircha bo'sh.",
            reply_markup=user_menu(),
        )
        return
    await message.answer(
        f"📚 <b>{label}</b>\n\nNomni tanlang:",
        reply_markup=pagination_keyboard(
            [(item.title, str(item.id)) for item in items],
            content_type,
            page,
            (page + 1) * 8 < total,
        ),
    )


async def edit_category(
    message: Message, database: Database, content_type: str, page: int
) -> None:
    items, total = await database.list_contents(content_type, offset=page * 8)
    if not items:
        await message.edit_text("Bu sahifada nomlar mavjud emas.")
        return
    label = {"movie": "Kinolar", "series": "Seriallar", "anime": "Animelar"}[content_type]
    await message.edit_text(
        f"📚 <b>{label}</b>\n\nNomni tanlang:",
        reply_markup=pagination_keyboard(
            [(item.title, str(item.id)) for item in items],
            content_type,
            page,
            (page + 1) * 8 < total,
        ),
    )


async def show_content(
    message: Message, database: Database, content: CatalogItem
) -> None:
    details = [f"🎞 <b>{escape_html(content.title)}</b>"]
    if content.year:
        details.append(f"📅 {content.year}")
    if content.genre:
        details.append(f"🏷 {escape_html(content.genre)}")
    if content.description:
        details.append(f"\n{escape_html(content.description)}")

    if content.content_type == "series":
        episodes = await database.list_episodes(content.id)
        if not episodes:
            details.append("\n\nQismlar tez orada qo'shiladi.")
        else:
            details.append(f"\n\n📺 Qismlar: {len(episodes)}")
        await message.edit_text(
            "\n".join(details),
            reply_markup=episode_keyboard(
                [(episode.id, episode.episode_number, episode.title) for episode in episodes],
            ),
        )
    else:
        await message.edit_text(
            "\n".join(details),
            reply_markup=content_detail_keyboard(
                content.content_type,
                content.id,
                bool(content.file_id and content.media_type),
            ),
        )


def register_admin_handlers(
    router: Router, database: Database, settings: Settings
) -> None:
    @router.message(Command("admin"))
    async def admin_command(message: Message, state: FSMContext) -> None:
        if not is_admin(message.from_user.id, settings):
            await message.answer("Bu buyruq faqat administrator uchun.")
            return
        await state.clear()
        await message.answer(
            "⚙️ <b>Admin panel</b>\nAmalni tanlang:", reply_markup=admin_menu()
        )

    @router.message(F.from_user.id == settings.admin_id, F.text == CANCEL_BUTTON)
    async def cancel_form(message: Message, state: FSMContext) -> None:
        await state.clear()
        await message.answer("Amal bekor qilindi.", reply_markup=admin_menu())

    @router.message(F.text == ADMIN_PANEL_BUTTON)
    async def admin_panel_button(message: Message, state: FSMContext) -> None:
        if not is_admin(message.from_user.id, settings):
            return
        await state.clear()
        await message.answer(
            "⚙️ <b>Admin panel</b>\nAmalni tanlang:", reply_markup=admin_menu()
        )

    @router.message(F.text == MANDATORY_MEMBERSHIP_BUTTON)
    async def mandatory_membership_panel(
        message: Message, state: FSMContext
    ) -> None:
        if not is_admin(message.from_user.id, settings):
            return
        await state.clear()
        await message.answer(
            "📢 <b>Majburiy a'zolik</b>\nAmalni tanlang:",
            reply_markup=mandatory_channels_menu(),
        )

    @router.message(F.text == BACK_ADMIN_BUTTON)
    async def back_to_admin_panel(message: Message, state: FSMContext) -> None:
        if not is_admin(message.from_user.id, settings):
            return
        await state.clear()
        await message.answer(
            "⚙️ <b>Admin panel</b>\nAmalni tanlang:", reply_markup=admin_menu()
        )

    @router.message(F.text == ADD_CHANNEL_BUTTON)
    async def start_channel_form(message: Message, state: FSMContext) -> None:
        if not is_admin(message.from_user.id, settings):
            return
        await state.clear()
        await state.set_state(ChannelForm.channel_id)
        await message.answer(
            "1/3. Kanal username yoki Telegram channel ID sini yuboring.\n"
            "Masalan: <code>@kanal_username</code> yoki <code>-1001234567890</code>.",
            reply_markup=cancel_keyboard(),
        )

    @router.message(ChannelForm.channel_id)
    async def channel_id_step(message: Message, state: FSMContext) -> None:
        if not is_admin(message.from_user.id, settings):
            return
        channel_id = normalise_channel_id(message.text)
        if not channel_id:
            await message.answer("Kanal username yoki ID sini yuboring.")
            return
        await state.update_data(channel_id=channel_id)
        await state.set_state(ChannelForm.name)
        await message.answer("2/3. Kanal nomini yuboring:")

    @router.message(ChannelForm.name)
    async def channel_name_step(message: Message, state: FSMContext) -> None:
        if not is_admin(message.from_user.id, settings):
            return
        name = (message.text or "").strip()
        if not name:
            await message.answer("Kanal nomi bo'sh bo'lishi mumkin emas.")
            return
        await state.update_data(name=name)
        await state.set_state(ChannelForm.url)
        await message.answer(
            "3/3. Kanal havolasini yuboring.\n"
            "Masalan: <code>https://t.me/kanal_username</code>."
        )

    @router.message(ChannelForm.url)
    async def channel_url_step(message: Message, state: FSMContext) -> None:
        if not is_admin(message.from_user.id, settings):
            return
        url = (message.text or "").strip()
        if not url:
            await message.answer("Kanal havolasi bo'sh bo'lishi mumkin emas.")
            return
        data = await state.get_data()
        try:
            channel_db_id = await database.add_mandatory_channel(
                channel_id=data["channel_id"],
                name=data["name"],
                url=url,
            )
        except sqlite3.IntegrityError:
            await state.clear()
            await message.answer(
                "Bu kanal allaqachon majburiy kanallar ro'yxatida.",
                reply_markup=mandatory_channels_menu(),
            )
            return
        await state.clear()
        await message.answer(
            f"✅ <b>{escape_html(data['name'])}</b> majburiy kanal sifatida qo'shildi.\n"
            f"ID: <code>{channel_db_id}</code>",
            reply_markup=mandatory_channels_menu(),
        )

    @router.message(F.text == LIST_CHANNELS_BUTTON)
    async def list_channels(message: Message, state: FSMContext) -> None:
        if not is_admin(message.from_user.id, settings):
            return
        await state.clear()
        channels = await database.list_mandatory_channels()
        if not channels:
            await message.answer(
                "📭 Majburiy kanallar ro'yxati bo'sh.",
                reply_markup=mandatory_channels_menu(),
            )
            return
        lines = ["📋 <b>Majburiy kanallar ro'yxati</b>\n"]
        for number, channel in enumerate(channels, start=1):
            lines.append(
                f"{number}. <b>{escape_html(channel.name)}</b>\n"
                f"   ID: <code>{escape_html(channel.channel_id)}</code>\n"
                f"   Havola: {escape_html(channel.url)}"
            )
        await message.answer(
            "\n\n".join(lines), reply_markup=mandatory_channels_menu()
        )

    @router.message(F.text == DELETE_CHANNEL_BUTTON)
    async def start_delete_channel(message: Message, state: FSMContext) -> None:
        if not is_admin(message.from_user.id, settings):
            return
        await state.clear()
        channels = await database.list_mandatory_channels()
        if not channels:
            await message.answer(
                "O'chirish uchun majburiy kanal mavjud emas.",
                reply_markup=mandatory_channels_menu(),
            )
            return
        await message.answer(
            "O'chirish uchun kanalni tanlang:",
            reply_markup=channel_delete_menu(
                [(channel.id, channel.name) for channel in channels]
            ),
        )

    @router.callback_query(F.data.startswith("admin:delete_channel:"))
    async def delete_channel_callback(
        callback: CallbackQuery, state: FSMContext
    ) -> None:
        if not is_admin(callback.from_user.id, settings):
            return
        await safe_answer(callback)
        channel_id = int(callback.data.rsplit(":", 1)[1])
        deleted = await database.delete_mandatory_channel(channel_id)
        await state.clear()
        if callback.message:
            await callback.message.edit_text(
                "✅ Kanal o'chirildi." if deleted else "Bu kanal topilmadi."
            )
            await callback.message.answer(
                "Majburiy a'zolik bo'limi:", reply_markup=mandatory_channels_menu()
            )

    @router.message(
        F.text.in_({ADD_MOVIE_BUTTON, ADD_ANIME_BUTTON, ADD_SERIES_BUTTON})
    )
    async def start_content_form(message: Message, state: FSMContext) -> None:
        if not is_admin(message.from_user.id, settings):
            return
        content_map = {
            ADD_MOVIE_BUTTON: "movie",
            ADD_ANIME_BUTTON: "anime",
            ADD_SERIES_BUTTON: "series",
        }
        await state.clear()
        await state.update_data(content_type=content_map[message.text])
        await state.set_state(ContentForm.title)
        await message.answer("Nomini yuboring:", reply_markup=cancel_keyboard())

    @router.message(ContentForm.title)
    async def content_title(message: Message, state: FSMContext) -> None:
        if not is_admin(message.from_user.id, settings):
            return
        title = (message.text or "").strip()
        if not title:
            await message.answer("Nom bo'sh bo'lishi mumkin emas.")
            return
        await state.update_data(title=title)
        await state.set_state(ContentForm.description)
        await message.answer("Tavsif yuboring yoki <code>skip</code> deb yozing:")

    @router.message(ContentForm.description)
    async def content_description(message: Message, state: FSMContext) -> None:
        if not is_admin(message.from_user.id, settings):
            return
        await state.update_data(description=optional_text(message.text))
        await state.set_state(ContentForm.year)
        await message.answer("Chiqarilgan yilni yuboring yoki <code>skip</code> deb yozing:")

    @router.message(ContentForm.year)
    async def content_year(message: Message, state: FSMContext) -> None:
        if not is_admin(message.from_user.id, settings):
            return
        year = parse_optional_year(message.text)
        if message.text and message.text.lower().strip() != "skip" and year is None:
            await message.answer("4 xonali to'g'ri yil yuboring yoki <code>skip</code> deb yozing:")
            return
        await state.update_data(year=year)
        await state.set_state(ContentForm.genre)
        await message.answer("Janrlarni vergul bilan ajratib yuboring yoki <code>skip</code> deb yozing:")

    @router.message(ContentForm.genre)
    async def content_genre(message: Message, state: FSMContext) -> None:
        if not is_admin(message.from_user.id, settings):
            return
        data = await state.get_data()
        genre = optional_text(message.text)
        if data["content_type"] == "series":
            content_id = await database.add_content(
                content_type=data["content_type"],
                title=data["title"],
                description=data["description"],
                year=data["year"],
                genre=genre,
                file_id=None,
                media_type=None,
            )
            await state.clear()
            await message.answer(
                f"✅ <b>{escape_html(data['title'])}</b> serial sifatida qo'shildi "
                f"(ID: <code>{content_id}</code>).",
                reply_markup=admin_menu(),
            )
            return
        await state.update_data(genre=genre)
        await state.set_state(ContentForm.file_id)
        await message.answer(
            "Kino yoki anime videosini yuboring yoki boshqa kanaldan forward qiling."
        )

    @router.message(ContentForm.file_id)
    async def content_file_id(message: Message, state: FSMContext) -> None:
        if not is_admin(message.from_user.id, settings):
            return
        if message.video:
            file_id = message.video.file_id
            media_type = "video"
        elif message.document:
            file_id = message.document.file_id
            media_type = "document"
        else:
            await message.answer(
                "Iltimos, video yuboring yoki video/document ko'rinishidagi "
                "xabarni forward qiling."
            )
            return

        data = await state.get_data()
        content_id = await database.add_content(
            content_type=data["content_type"],
            title=data["title"],
            description=data["description"],
            year=data["year"],
            genre=data["genre"],
            file_id=file_id,
            media_type=media_type,
        )
        await state.clear()
        await message.answer(
            f"✅ <b>{escape_html(data['title'])}</b> qo'shildi "
            f"(ID: <code>{content_id}</code>).",
            reply_markup=admin_menu(),
        )

    @router.message(ContentForm.media_type)
    async def content_media_type(message: Message, state: FSMContext) -> None:
        if not is_admin(message.from_user.id, settings):
            return
        media_type = normalise_media_type(message.text)
        if media_type is None:
            await message.answer("Faqat video, document yoki audio dan birini yuboring.")
            return
        data = await state.get_data()
        content_id = await database.add_content(
            content_type=data["content_type"],
            title=data["title"],
            description=data["description"],
            year=data["year"],
            genre=data["genre"],
            file_id=data["file_id"],
            media_type=media_type,
        )
        await state.clear()
        await message.answer(
            f"✅ <b>{escape_html(data['title'])}</b> qo'shildi "
            f"(ID: <code>{content_id}</code>).",
            reply_markup=admin_menu(),
        )

    @router.message(F.text == ADD_EPISODE_BUTTON)
    async def start_episode_form(message: Message, state: FSMContext) -> None:
        if not is_admin(message.from_user.id, settings):
            return
        series = await database.list_series()
        if not series:
            await message.answer(
                "Qism qo'shishdan oldin kamida bitta serial qo'shing.",
                reply_markup=admin_menu(),
            )
            return
        await state.clear()
        await state.set_state(EpisodeForm.choose_series)
        await message.answer(
            "Bu qism tegishli bo'lgan serialni tanlang:",
            reply_markup=series_picker([(item.id, item.title) for item in series]),
        )

    @router.callback_query(F.data.startswith("admin:episode_series:"))
    async def choose_episode_series(callback: CallbackQuery, state: FSMContext) -> None:
        if not is_admin(callback.from_user.id, settings):
            return
        await safe_answer(callback)
        series_id = int(callback.data.rsplit(":", 1)[1])
        series = await database.get_content(series_id)
        if not series or series.content_type != "series":
            if callback.message:
                await callback.message.answer("Bu serial endi mavjud emas.")
            return
        await state.update_data(series_id=series_id, series_title=series.title)
        await state.set_state(EpisodeForm.episode_number)
        if callback.message:
            await callback.message.edit_text(
                f"<b>{escape_html(series.title)}</b> serialiga qism qo'shish.\n"
                "Qism raqamini yuboring:"
            )

    @router.message(EpisodeForm.episode_number)
    async def episode_number(message: Message, state: FSMContext) -> None:
        if not is_admin(message.from_user.id, settings):
            return
        try:
            number = int((message.text or "").strip())
            if number < 1:
                raise ValueError
        except ValueError:
            await message.answer("Musbat butun qism raqamini yuboring.")
            return
        await state.update_data(episode_number=number)
        await state.set_state(EpisodeForm.title)
        await message.answer("Qism nomini yuboring:")

    @router.message(EpisodeForm.title)
    async def episode_title(message: Message, state: FSMContext) -> None:
        if not is_admin(message.from_user.id, settings):
            return
        title = (message.text or "").strip()
        if not title:
            await message.answer("Qism nomi bo'sh bo'lishi mumkin emas.")
            return
        await state.update_data(title=title)
        await state.set_state(EpisodeForm.description)
        await message.answer("Tavsif yuboring yoki <code>skip</code> deb yozing:")

    @router.message(EpisodeForm.description)
    async def episode_description(message: Message, state: FSMContext) -> None:
        if not is_admin(message.from_user.id, settings):
            return
        await state.update_data(description=optional_text(message.text))
        await state.set_state(EpisodeForm.file_id)
        await message.answer("Bu qismning Telegram file ID sini yuboring:")

    @router.message(EpisodeForm.file_id)
    async def episode_file_id(message: Message, state: FSMContext) -> None:
        if not is_admin(message.from_user.id, settings):
            return
        file_id = (message.text or "").strip()
        if len(file_id) < 10:
            await message.answer("File ID juda qisqa. To'liq file ID ni yuboring.")
            return
        await state.update_data(file_id=file_id)
        await state.set_state(EpisodeForm.media_type)
        await message.answer(
            "Media turini yuboring: <code>video</code>, <code>document</code> yoki <code>audio</code>."
        )

    @router.message(EpisodeForm.media_type)
    async def episode_media_type(message: Message, state: FSMContext) -> None:
        if not is_admin(message.from_user.id, settings):
            return
        media_type = normalise_media_type(message.text)
        if media_type is None:
            await message.answer("Faqat video, document yoki audio dan birini yuboring.")
            return
        data = await state.get_data()
        try:
            episode_id = await database.add_episode(
                series_id=data["series_id"],
                episode_number=data["episode_number"],
                title=data["title"],
                description=data["description"],
                file_id=data["file_id"],
                media_type=media_type,
            )
        except Exception as error:
            if "UNIQUE constraint failed" in str(error):
                await message.answer(
                    "Bu serialda ushbu qism raqami allaqachon mavjud. "
                    "Bekor qilib, boshqa raqam tanlang."
                )
                return
            raise
        await state.clear()
        await message.answer(
            f"✅ Qism qo'shildi (ID: <code>{episode_id}</code>).",
            reply_markup=admin_menu(),
        )

    @router.message(F.text == CATALOG_STATS_BUTTON)
    async def catalog_stats(message: Message) -> None:
        if not is_admin(message.from_user.id, settings):
            return
        stats = await database.stats()
        await message.answer(
            "📊 <b>Katalog statistikasi</b>\n\n"
            f"🎬 Kinolar: <b>{stats['movies']}</b>\n"
            f"📺 Seriallar: <b>{stats['series']}</b>\n"
            f"🍥 Animelar: <b>{stats['anime']}</b>\n"
            f"🧩 Qismlar: <b>{stats['episodes']}</b>\n"
            f"👥 Foydalanuvchilar: <b>{stats['users']}</b>",
            reply_markup=admin_menu(),
        )

    @router.callback_query(F.data == "admin:cancel")
    async def cancel_callback(callback: CallbackQuery, state: FSMContext) -> None:
        if not is_admin(callback.from_user.id, settings):
            return
        await safe_answer(callback)
        await state.clear()
        if callback.message:
            await callback.message.edit_text("Amal bekor qilindi.")
            await callback.message.answer("Admin panel:", reply_markup=admin_menu())


def cancel_keyboard():
    from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=CANCEL_BUTTON)]],
        resize_keyboard=True,
    )


async def send_media(
    bot: Bot, chat_id: int, file_id: str, media_type: str, caption: str
) -> None:
    if media_type == "video":
        await bot.send_video(chat_id, video=file_id, caption=caption)
    elif media_type == "audio":
        await bot.send_audio(chat_id, audio=file_id, caption=caption)
    else:
        await bot.send_document(chat_id, document=file_id, caption=caption)


def optional_text(value: str | None) -> str:
    text = (value or "").strip()
    return "" if text.lower() == "skip" else text


def parse_optional_year(value: str | None) -> int | None:
    text = (value or "").strip()
    if text.lower() == "skip" or not text:
        return None
    if len(text) != 4 or not text.isdigit():
        return None
    year = int(text)
    return year if 1888 <= year <= 2200 else None


def normalise_media_type(value: str | None) -> str | None:
    text = (value or "").strip().lower()
    return text if text in {"video", "document", "audio"} else None


def normalise_channel_id(value: str | None) -> str:
    text = (value or "").strip()
    if text.startswith("https://t.me/"):
        username = text.removeprefix("https://t.me/").split("/", 1)[0]
        return f"@{username}" if not username.startswith("@") else username
    if text.startswith("@") or text.startswith("-") or text.isdigit():
        return text
    return f"@{text}" if text else ""


def escape_html(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )