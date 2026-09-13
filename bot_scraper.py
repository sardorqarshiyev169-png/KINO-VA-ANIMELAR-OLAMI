import os
import re
import asyncio
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

from pyrogram import Client
from bot.config import Settings
from bot.database import Database
from userbot_config import API_ID, API_HASH, DUMP_CHANNEL_ID

# Baza bilan ulanish (Asosiy bot bazasi)
settings = Settings.from_env()
db = Database(settings.database_path)

# Userbot sessiyasini yaratamiz
# Removed global app instantiation

TARGET_BOT = "@tarjima_kinolar_uzgobot"

async def parse_caption(caption: str):
    """
    Kino matnidan Nomi, yili va tavsifini ajratib olish va tozalash.
    """
    if not caption:
        return "Noma'lum kino", "Noma'lum", "🎥 Tarjima kino"
        
    # REKLAMALARNI TOZALASH (Boshqa kanallar va ssilkalarini olib tashlaymiz)
    # @kanal_nomi, t.me/kanal_nomi, https://... larni o'chiradi
    clean_desc = re.sub(r'(@[a-zA-Z0-9_]+)', '', caption)
    clean_desc = re.sub(r'(https?://\S+)', '', clean_desc)
    clean_desc = re.sub(r'(t\.me/\S+)', '', clean_desc)
    
    title = "Noma'lum kino"
    year = "2024"
    
    lines = clean_desc.split('\n')
    for line in lines:
        if "nomi" in line.lower() or "kino:" in line.lower():
            title = line.split(":", 1)[-1].strip()
        elif "yili" in line.lower() or "yil:" in line.lower():
            year_match = re.search(r'\d{4}', line)
            if year_match:
                year = year_match.group()
                
    if title == "Noma'lum kino" and lines:
        # Reklamalardan tozalangan matnning eng birinchi qatorini nom deb olamiz
        for line in lines:
            if line.strip():
                title = line.replace('🎬', '').replace('🎥', '').strip()
                title = title[:50]
                break

    # Yozuvni (Tavsifni) yanada chiroyli va toza qilish
    final_desc = "\n".join([line for line in clean_desc.split('\n') if line.strip() != ""])
    final_desc = f"🎬 Nomi: {title}\n📅 Yili: {year}\n\n{final_desc}\n\n🤖 @SizningBotingiz_Uchun"
    
    return title, year, final_desc

async def scrape_bot(start_code=1, end_code=10):
    app = Client(
        "my_account",
        api_id=API_ID,
        api_hash=API_HASH
    )
    
    print(f"{TARGET_BOT} botidan kinolarni o'g'irlash boshlandi (KODLAR: {start_code}-{end_code})...")
    
    await db.initialize()
    
    async with app:
        count = 0
        
        for code in range(start_code, end_code + 1):
            try:
                print(f"[{code}] - kod jo'natilmoqda...")
                await app.send_message(TARGET_BOT, str(code))
                
                await asyncio.sleep(2.5)
                
                movie_found = False
                async for message in app.get_chat_history(TARGET_BOT, limit=3):
                    if not message.outgoing and (message.video or message.document):
                        print(f"Video keldi! Tozalanmoqda...")
                        
                        title, year, description = await parse_caption(message.caption)
                        
                        copied = await message.copy(DUMP_CHANNEL_ID, caption=description) # Yangi toza caption bilan yuklaymiz!
                        file_id = ""
                        
                        if copied.video or copied.document:
                            file_id = str(copied.id)  # Save the message ID!
                            
                        if file_id:
                            # 5. Bazaga kiritish (kutish bilan)
                            new_id = await db.add_content(
                                content_type="movie",
                                title=title,
                                description=description,
                                year=int(year) if year.isdigit() else None,
                                genre="",
                                file_id=file_id,
                                media_type="video"
                            )
                            count += 1
                            print(f"BAZAGA QO'SHILDI: {title} | Botingizdagi yangi KOD: {new_id}")
                            movie_found = True
                        break
                
                if not movie_found:
                    print(f"[{code}] kodida kino yo'q yoki bot javob bermadi.")
                    
            except Exception as e:
                print(f"Xatolik yuz berdi ({code}):", e)
                await asyncio.sleep(5)
                
        print(f"\nJARAYON TUGADI! Jami {count} ta kino ko'chirildi va tozalab joylandi.")

if __name__ == "__main__":
    import sys
    
    start = 50
    end = 900
    
    if len(sys.argv) >= 3:
        try:
            start = int(sys.argv[1])
            end = int(sys.argv[2])
        except ValueError:
            pass

    asyncio.run(scrape_bot(start_code=start, end_code=end))
