from aiogram import Bot
from database import get_channels


async def is_subscribed_all(bot: Bot, user_id: int) -> bool:
    channels = await get_channels()
    if not channels:
        return True  # kanal qo'shilmagan bo'lsa, tekshirmaydi

    for ch in channels:
        _, chat_id, username, title = ch
        try:
            member = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
            if member.status in ("left", "kicked"):
                return False
        except Exception:
            # Bot kanalda admin bo'lmasa yoki xato bo'lsa, xavfsizlik uchun False qaytaramiz
            return False
    return True
