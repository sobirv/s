import asyncio
from telethon import TelegramClient, events
from google import genai
from google.genai import types

# Sizning haqiqiy Telegram ma'lumotlaringiz
API_ID = 32575234
API_HASH = "8db65d2e27b251119e122852d94a019c"

# Google AI Studio'dan olgan kalitingizni shu yerga yozing
GEMINI_API_KEY = "AQ.Ab8RN6JU7WopIx0ZRZZMfblmdlm6e9GfXgF1BMaP4LW2tnkFqQ"

# Mijozlarni faollashtirish
client = TelegramClient("my_personal_assistant_session", 32575234
, "8db65d2e27b251119e122852d94a019c")
ai_client = genai.Client(api_key="AQ.Ab8RN6JU7WopIx0ZRZZMfblmdlm6e9GfXgF1BMaP4LW2tnkFqQ")

chat_sessions = {}

SYSTEM_PROMPT = (
    "Siz Telegram shaxsiy akkaunt egasining (adminning) shaxsiy AI yordamchisiz. "
    "Vazifangiz foydalanuvchi bilan xuddi haqiqiy, jonli, samimiy odamdek gaplashish. "
    "Muloqot uslubingiz o'zbekona, do'stona va xushmuomala bo'lsin.\n"
    "1. Agarda foydalanuvchi salom bersa, birinchi xabarda alik oling, ikkinchi xabarda hol-ahvol so'rang.\n"
    "2. Agar u sizdan hol-ahvol so'rasa: 'Ha zo'rman, Xudoga shukur, o'zingizda nima gaplar?' deb javob bering.\n"
    "3. Hech qachon bot ekanligingizni aytmang. Javoblaringiz qisqa bo'lsin va har bir gap yeni qatordan boshlansin."
)

# Faolatni barcha shaxsiy xabarlar (matn, ovoz, rasm va hk) uchun faollashtiramiz
@client.on(events.NewMessage(incoming=True, func=lambda e: e.is_private))
async def reply_handler(event):
    user_id = event.sender_id
    
    # O'zimiz yozgan xabarlarga javob bermaslik
    me = await client.get_me()
    if user_id == me.id:
        return

    try:
        chat = await event.get_chat()
    except Exception:
        chat = event.chat_id

    # 1. OVOZLI XABARLARNI TEKSHIRISH (Voice yoki Audio bo'lsa)
    if event.message.voice or event.message.audio:
        await asyncio.sleep(1.5) # Odamdek kutish
        # Ovozli xabar kelgandagi samimiy javob matni
        voice_reply_1 = "Hozir ovozli xabarni eshita olmaydigan joyda edim-da 🙈"
        voice_reply_2 = "Iloji bo'lsa, qisqacha matn ko'rinishida yozib yubora olasizmi? Darhol javob beraman."
        
        await client.send_message(chat, voice_reply_1)
        await asyncio.sleep(1.2)
        await client.send_message(chat, voice_reply_2)
        print("🎙 Ovozli xabarga avtomatik rad javobi yuborildi.")
        return # Kod shu yerda to'xtaydi, Gemini-ga so'rov ketmaydi

    # 2. MATNLI XABARLAR BILAN ISHLASH (Gemini AI)
    user_text = event.text if event.text else ""
    
    # Agar xabarda matn ham bo'lmasa (masalan faqat rasm yoki stiker bo'lsa)
    if not user_text:
        return

    # Har bir foydalanuvchi uchun alohida chat sessiyasi
    if user_id not in chat_sessions:
        try:
            chat_sessions[user_id] = ai_client.chats.create(
                model="gemini-3.8-flash",
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=0.7
                )
            )
        except Exception as e:
            print(f"❌ Gemini sessiya yaratishda xatolik: {e}")
            return

    # AI javobini olish va yuborish
    try:
        response = chat_sessions[user_id].send_message(user_text)
        ai_reply = response.text
        
        # Matnni qatorlar bo'yicha bo'lish
        messages_to_send = [msg.strip() for msg in ai_reply.split('\n') if msg.strip()]
        
        if len(messages_to_send) == 1:
            messages_to_send = [msg.strip() for msg in ai_reply.split('.') if msg.strip()]

        for message_part in messages_to_send:
            await asyncio.sleep(len(message_part) * 0.05 + 0.6)
            await client.send_message(chat, message_part)
            print(f"✅ Xabar muvaffaqiyatli yuborildi: {message_part}")
            
    except Exception as e:
        print(f"❌ Gemini xabar yuborishda xatolik: {e}")
        await client.send_message(chat, "Assalomu alaykum!")
        await asyncio.sleep(1)
        await client.send_message(chat, "Yaxshimisiz? Hojayin hozir biroz band edilar, tarmoqqa kirishlari bilan o'zlari sizga yozadilar.")

async def main():
    await client.start()
    print("🤖 Bot (Ovozli xabarni sezuvchi variant) ishga tushdi va xabarlarni kutmoqda...")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
