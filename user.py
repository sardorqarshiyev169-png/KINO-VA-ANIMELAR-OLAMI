from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart

from states import UserStates
from keyboards import main_menu_kb, subscription_kb
from subscription import is_subscribed_all
from database import (
    add_user,
    get_channels,
    get_movie_by_code,
    get_anime_by_code,
)

router = Router()


async def send_subscription_prompt(message: Message):
    channels = await get_channels()
    await message.answer(
        "📢 Botdan foydalanish uchun quyidagi kanal(lar)ga obuna bo'ling, "
        "so'ng \"✅ Tekshirish\" tugmasini bosing:",
        reply_markup=subscription_kb(channels),
    )


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await add_user(
        message.from_user.id,
        message.from_user.username or "",
        message.from_user.full_name or "",
    )

    if not await is_subscribed_all(message.bot, message.from_user.id):
        await send_subscription_prompt(message)
        return

    await message.answer(
        "🎬 Assalomu alaykum!\n\nQuyidagi bo'limlardan birini tanlang:",
        reply_markup=main_menu_kb(),
    )


@router.callback_query(F.data == "check_sub")
async def check_subscription_cb(callback: CallbackQuery, state: FSMContext):
    if await is_subscribed_all(callback.bot, callback.from_user.id):
        await callback.message.delete()
        await callback.message.answer(
            "✅ Obuna tasdiqlandi! Bo'limni tanlang:",
            reply_markup=main_menu_kb(),
        )
    else:
        await callback.answer(
            "❌ Siz hali barcha kanallarga obuna bo'lmagansiz!", show_alert=True
        )


@router.message(F.text == "🎬 Kino")
async def menu_kino(message: Message, state: FSMContext):
    if not await is_subscribed_all(message.bot, message.from_user.id):
        await send_subscription_prompt(message)
        return
    await state.set_state(UserStates.waiting_movie_code)
    await message.answer("🎬 Kino kodini kiriting (masalan: 101):")


@router.message(F.text == "🎭 Anime")
async def menu_anime(message: Message, state: FSMContext):
    if not await is_subscribed_all(message.bot, message.from_user.id):
        await send_subscription_prompt(message)
        return
    await state.set_state(UserStates.waiting_anime_code)
    await message.answer("🎭 Anime kodini kiriting (masalan: 201):")


@router.message(UserStates.waiting_movie_code)
async def get_movie(message: Message, state: FSMContext):
    code = message.text.strip()
    result = await get_movie_by_code(code)
    if result:
        file_id, title = result
        await message.answer_video(file_id, caption=f"🎬 {title}\nKod: {code}")
    else:
        await message.answer("❌ Bunday kodli kino topilmadi. Qaytadan urinib ko'ring.")


@router.message(UserStates.waiting_anime_code)
async def get_anime(message: Message, state: FSMContext):
    code = message.text.strip()
    result = await get_anime_by_code(code)
    if result:
        file_id, title = result
        await message.answer_video(file_id, caption=f"🎭 {title}\nKod: {code}")
    else:
        await message.answer("❌ Bunday kodli anime topilmadi. Qaytadan urinib ko'ring.")
