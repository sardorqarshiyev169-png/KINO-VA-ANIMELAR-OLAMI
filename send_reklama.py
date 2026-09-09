import asyncio
import aiosqlite
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

# BU YERGA O'Z BOT TOKENINGIZNI YOZING
BOT_TOKEN = "8639175369:AAELAae_OJ7a5nxn1Qz7V2IGUdLZCumwjI0"
DB_NAME = "database.db"
PHOTO_PATH = "reklama.jpg"  # Rasmni shu nom bilan loyiha papkasiga saqlang

CAPTION = """🔥 **Bozzni yoring! Botimizga yana bir yangi va ajoyib kino qo'shildi!** 🔥

🎬 **Kino nomi:** Miss Peregrinening noyob qobiliyatli bolalar uyi 
🎭 **Janr:** Fantastika, Sarguzasht, Oilaviy
🌟 **Sifat:** HD 720p (Yuqori sifat)
🇺🇿 **Til:** O'zbek tilida (Tarjima)

📝 **Qisqacha mazmuni:**
Jeykob o'z bobosining g'alati sirlari izidan tushib, uzoq bir oroldagi sirli "Noyob qobiliyatli bolalar uyi"ni topadi. Bu joyda u nafaqat g'aroyib va sehrli bolalar bilan tanishadi, balki yovuz kuchlarga qarshi kurashishi kerakligini ham anglab yetadi. Hayajonli voqealar, sehrli olam va kutilmagan burilishlar sizni kutmoqda!

🍿 *Bo'sh vaqtingizni mazmunli o'tkazish uchun ajoyib tanlov!*

👉 **Kinoni yuklab olish uchun botga quyidagi kodni yuboring:**
🔢 **KOD:** `[Bu yerga kodni yozing, masalan 105]`

Do'stlaringizga ham ulashishni unutmang! 😉👇"""

async def get_all_user_ids():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT user_id FROM users")
        rows = await cursor.fetchall()
        return [r[0] for r in rows]

async def main():
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
    user_ids = await get_all_user_ids()
    print(f"Jami foydalanuvchilar: {len(user_ids)} ta. Yuborish boshlandi...")

    from aiogram.types import FSInputFile
    photo = FSInputFile(PHOTO_PATH)

    sent = 0
    failed = 0

    for uid in user_ids:
        try:
            await bot.send_photo(chat_id=uid, photo=photo, caption=CAPTION)
            sent += 1
        except Exception as e:
            print(f"Xato ({uid}): {e}")
            failed += 1
        
        await asyncio.sleep(0.1) # Limitdan oshib ketmaslik uchun

    print(f"✅ Tugadi! Yuborildi: {sent} | Yuborilmadi: {failed}")
    await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
