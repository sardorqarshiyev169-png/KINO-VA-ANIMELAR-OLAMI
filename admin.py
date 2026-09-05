import asyncio

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command

from config import ADMIN_IDS
from states import AdminStates
from keyboards import admin_panel_kb, channels_manage_kb, back_kb
from database import (
    add_movie,
    add_anime,
    delete_movie,
    delete_anime,
    get_users_count,
    get_users_today_count,
    get_users_month_count,
    get_all_user_ids,
    count_movies,
    count_animes,
    add_channel,
    get_channels,
    delete_channel,
)

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    await message.answer("🛠 Admin panel:", reply_markup=admin_panel_kb())


@router.callback_query(F.data == "admin_back")
async def admin_back(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("🛠 Admin panel:", reply_markup=admin_panel_kb())


# ---------- STATISTIKA ----------

@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    users = await get_users_count()
    users_today = await get_users_today_count()
    users_month = await get_users_month_count()
    movies = await count_movies()
    animes = await count_animes()
    text = (
        f"📊 Statistika:\n\n"
        f"🎬 Kinolar soni: {movies}\n"
        f"🎭 Animelar soni: {animes}\n\n"
        f"👥 Umumiy foydalanuvchilar: {users}\n"
        f"🟢 Bugun qo'shilganlar: {users_today}\n"
        f"🔵 Oxirgi 1 oyda qo'shilganlar: {users_month}"
    )
    await callback.message.edit_text(text, reply_markup=back_kb())


# ---------- KINO QO'SHISH ----------

@router.callback_query(F.data == "admin_add_movie")
async def admin_add_movie(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.waiting_movie_video)
    await callback.message.edit_text("🎬 Kino videosini yuboring:", reply_markup=back_kb())


@router.message(AdminStates.waiting_movie_video, F.video)
async def receive_movie_video(message: Message, state: FSMContext):
    await state.update_data(file_id=message.video.file_id)
    await state.set_state(AdminStates.waiting_movie_code)
    await message.answer(
        "✏️ Endi kino nomi va kodini shu formatda yuboring:\n"
        "<b>Nomi - Kod</b>\n\nMasalan: <i>Titanik - 101</i>",
        parse_mode="HTML",
    )


@router.message(AdminStates.waiting_movie_video)
async def wrong_movie_video(message: Message):
    await message.answer("❗️ Iltimos, video fayl yuboring.")


@router.message(AdminStates.waiting_movie_code)
async def receive_movie_code(message: Message, state: FSMContext):
    if " - " not in message.text:
        await message.answer("❗️ Format noto'g'ri. Namuna: Titanik - 101")
        return
    title, code = message.text.rsplit(" - ", 1)
    title, code = title.strip(), code.strip()
    data = await state.get_data()
    ok = await add_movie(code, data["file_id"], title)
    await state.clear()
    if ok:
        await message.answer(f"✅ Kino qo'shildi!\nNomi: {title}\nKod: {code}", reply_markup=admin_panel_kb())
    else:
        await message.answer(f"❌ Bu kod ({code}) allaqachon mavjud. Boshqa kod tanlang.", reply_markup=admin_panel_kb())


# ---------- ANIME QO'SHISH ----------

@router.callback_query(F.data == "admin_add_anime")
async def admin_add_anime(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.waiting_anime_video)
    await callback.message.edit_text("🎭 Anime videosini yuboring:", reply_markup=back_kb())


@router.message(AdminStates.waiting_anime_video, F.video)
async def receive_anime_video(message: Message, state: FSMContext):
    await state.update_data(file_id=message.video.file_id)
    await state.set_state(AdminStates.waiting_anime_code)
    await message.answer(
        "✏️ Endi anime nomi va kodini shu formatda yuboring:\n"
        "<b>Nomi - Kod</b>\n\nMasalan: <i>Naruto 1-qism - 201</i>",
        parse_mode="HTML",
    )


@router.message(AdminStates.waiting_anime_video)
async def wrong_anime_video(message: Message):
    await message.answer("❗️ Iltimos, video fayl yuboring.")


@router.message(AdminStates.waiting_anime_code)
async def receive_anime_code(message: Message, state: FSMContext):
    if " - " not in message.text:
        await message.answer("❗️ Format noto'g'ri. Namuna: Naruto 1-qism - 201")
        return
    title, code = message.text.rsplit(" - ", 1)
    title, code = title.strip(), code.strip()
    data = await state.get_data()
    ok = await add_anime(code, data["file_id"], title)
    await state.clear()
    if ok:
        await message.answer(f"✅ Anime qo'shildi!\nNomi: {title}\nKod: {code}", reply_markup=admin_panel_kb())
    else:
        await message.answer(f"❌ Bu kod ({code}) allaqachon mavjud. Boshqa kod tanlang.", reply_markup=admin_panel_kb())


# ---------- O'CHIRISH ----------

@router.callback_query(F.data == "admin_del_movie")
async def admin_del_movie(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.waiting_delete_movie_code)
    await callback.message.edit_text("🗑 O'chirmoqchi bo'lgan kino kodini yuboring:", reply_markup=back_kb())


@router.message(AdminStates.waiting_delete_movie_code)
async def do_delete_movie(message: Message, state: FSMContext):
    ok = await delete_movie(message.text.strip())
    await state.clear()
    if ok:
        await message.answer("✅ Kino o'chirildi.", reply_markup=admin_panel_kb())
    else:
        await message.answer("❌ Bunday kod topilmadi.", reply_markup=admin_panel_kb())


@router.callback_query(F.data == "admin_del_anime")
async def admin_del_anime(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.waiting_delete_anime_code)
    await callback.message.edit_text("🗑 O'chirmoqchi bo'lgan anime kodini yuboring:", reply_markup=back_kb())


@router.message(AdminStates.waiting_delete_anime_code)
async def do_delete_anime(message: Message, state: FSMContext):
    ok = await delete_anime(message.text.strip())
    await state.clear()
    if ok:
        await message.answer("✅ Anime o'chirildi.", reply_markup=admin_panel_kb())
    else:
        await message.answer("❌ Bunday kod topilmadi.", reply_markup=admin_panel_kb())


# ---------- XABAR YUBORISH (BROADCAST) ----------

@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.waiting_broadcast)
    await callback.message.edit_text(
        "📢 Barcha foydalanuvchilarga yubormoqchi bo'lgan xabaringizni yuboring "
        "(matn, rasm, video — barchasi qo'llab-quvvatlanadi):",
        reply_markup=back_kb(),
    )


@router.message(AdminStates.waiting_broadcast)
async def do_broadcast(message: Message, state: FSMContext, bot: Bot):
    await state.clear()
    user_ids = await get_all_user_ids()
    sent, failed = 0, 0
    status = await message.answer(f"⏳ Yuborilmoqda... (0/{len(user_ids)})")

    for i, uid in enumerate(user_ids, start=1):
        try:
            await message.copy_to(chat_id=uid)
            sent += 1
        except Exception:
            failed += 1
        if i % 25 == 0:
            await asyncio.sleep(1)  # flood limitdan qochish uchun

    await status.edit_text(f"✅ Xabar yuborildi!\n\n✔️ Yuborildi: {sent}\n❌ Yuborilmadi: {failed}")
    await message.answer("🛠 Admin panel:", reply_markup=admin_panel_kb())


# ---------- MAJBURIY KANALLAR ----------

@router.callback_query(F.data == "admin_channels")
async def admin_channels(callback: CallbackQuery):
    channels = await get_channels()
    text = "📡 Majburiy obuna kanallari:" if channels else "📡 Hozircha kanal qo'shilmagan."
    await callback.message.edit_text(text, reply_markup=channels_manage_kb(channels))


@router.callback_query(F.data == "add_channel")
async def add_channel_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.waiting_channel_input)
    await callback.message.edit_text(
        "➕ Kanal qo'shish uchun kanaldagi istalgan xabarni shu botga forward qiling.\n\n"
        "❗️ Diqqat: bot avval o'sha kanalga admin qilib qo'shilgan bo'lishi kerak!",
        reply_markup=back_kb(),
    )


@router.message(AdminStates.waiting_channel_input, F.forward_from_chat)
async def add_channel_finish(message: Message, state: FSMContext):
    chat = message.forward_from_chat
    await add_channel(str(chat.id), chat.username or "", chat.title or "")
    await state.clear()
    channels = await get_channels()
    await message.answer(
        f"✅ Kanal qo'shildi: {chat.title}",
    )
    await message.answer("📡 Majburiy obuna kanallari:", reply_markup=channels_manage_kb(channels))


@router.message(AdminStates.waiting_channel_input)
async def add_channel_wrong(message: Message):
    await message.answer("❗️ Iltimos, kanaldagi biror xabarni forward qiling.")


@router.callback_query(F.data.startswith("del_channel_"))
async def del_channel(callback: CallbackQuery):
    db_id = int(callback.data.replace("del_channel_", ""))
    await delete_channel(db_id)
    channels = await get_channels()
    await callback.message.edit_text(
        "📡 Majburiy obuna kanallari:" if channels else "📡 Hozircha kanal qo'shilmagan.",
        reply_markup=channels_manage_kb(channels),
    )
