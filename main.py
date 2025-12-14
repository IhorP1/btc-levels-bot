import os
from telegram import Bot

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = Bot(token=TELEGRAM_TOKEN)

try:
    bot.send_message(chat_id=CHAT_ID, text="ТЕСТ: Бот работает! Если видишь это — всё ок 🚀")
    print("Тестовое сообщение отправлено!")
except Exception as e:
    print(f"ОШИБКА: {e}")
