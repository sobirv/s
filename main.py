import asyncio
import os
import threading
from http.server import SimpleHTTPRequestHandler, HTTPServer
from telethon import TelegramClient, events
from google import genai
from google.genai import types

# 1. RENDER TEKIN WEB SERVICE-DA O'CHIB QOLMASLIGI UCHUN SOXTA PORT OCHISH
def run_dummy_server():
    try:
        port = int(os.environ.get("PORT", 10000))
        server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
        print(f"🌍 Soxta veb-port {port} da ishga tushdi.")
        server.serve_forever()
    except Exception as e:
        print(f"Soxta serverda xatolik: {e}")

# Portni alohida oqimda (fonda) ishga tushiramiz
threading.Thread(target=run_dummy_server, daemon=True).start()


# 2. TELEGRAM VA GEMINI SOZLAMALARI
API_ID = 32575234
API_HASH = "8db65d2e27b251119e122852d94a019c"

# ⚠️ DIQQAT: BU YERGA O'ZINGIZNING GOOGLE API KALITINGIZNI YOZING
GEMINI_API_KEY = "AQ.Ab8RN6Ls_NT07oG2KEQoaJ0eQp284PpNGqvgeS9khv_8tJb3Bg"

# Mijozlarni faollashtirish
client = TelegramClient("my_personal_assistant_session", 32575234
, '8db65d2e27b251119e122852d94a019c')
ai_client = genai.Client(api_key='AQ.Ab8RN6Ls_NT07oG2KEQoaJ0eQp284PpNGqvgeS9khv_8tJb3Bg')

chat_sessions = {}

SYSTEM_PROMPT = (
    "Siz Telegram shaxsiy akkaunt egasining (adminning) shaxsiy AI yordamchisiz. "
    "Vazifangiz foydalanuvchi bilan xuddi haqiqiy, jonli, samimiy odamdek gaplashish. "
    "Muloqot uslubingiz o'zbekona, do'stona va xushmuomala bo'lsin.\n"
    "1. Agarda foydalanuvchi salom bersa, birinchi xabarda alik oling, ikkinchi xabarda hol-ahvol so'rang.\n"
    "2. Agar u sizdan hol-ahvol so'rasa: 'Ha zo'rman, Xudoga shukur, o'zingizda nima gaplar?' deb javob bering.\n"
    "3. Hech qachon bot ekanligingizni aytmang. Javoblaringiz qisqa bo'lsin va har bir gap yangi qatordan boshlansin."
)

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

    # OVOZLI XABARLARNI TEKSHIRISH
    if event.message.voice or event.message.audio:
        await asyncio.sleep(1.5)
        await client.send_message(chat, "Hozir ovozli xabarni eshita olmaydigan joyda edim-da 🙈")
        await asyncio.sleep(1.2)
        await client.send_message(chat, "Iloji bo'lsa, qisqacha matn ko'rinishida yozib yubora olasizmi? Darhol javob beraman.")
        return

    # MATNLI XABARLAR BILAN ISHLASH
    user_text = event.text if event.text else ""
    if not user_text:
        return

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

    try:
        response = chat_sessions[user_id].send_message(user_text)
        ai_reply = response.text
        
        messages_to_send = [msg.strip() for msg in ai_reply.split('\n') if msg.strip()]
        if len(messages_to_send) == 1:
            messages_to_send = [msg.strip() for msg in ai_reply.split('.') if msg.strip()]

        for message_part in messages_to_send:
            await asyncio.sleep(len(message_part) * 0.05 + 0.6)
            await client.send_message(chat, message_part)
            print(f"✅ Xabar yuborildi: {message_part}")
            
    except Exception as e:
        print(f"❌ Gemini xatoligi: {e}")
        await client.send_message(chat, "Assalomu alaykum!")
        await asyncio.sleep(1)
        await client.send_message(chat, "Yaxshimisiz? Hojayin hozir biroz band edilar, tarmoqqa kirishlari bilan o'zlari sizga yozadilar.")

async def main():
    await client.start()
    print("🤖 Bot (Port integratsiyasi bilan) muvaffaqiyatli ishga tushdi...")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
