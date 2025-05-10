import os
from telegram import Bot

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

print("Запуск скрипта...")
print("TELEGRAM_TOKEN:", bool(TELEGRAM_TOKEN))
print("CHAT_ID:", CHAT_ID)

try:
    bot = Bot(token=TELEGRAM_TOKEN)
    bot.send_message(chat_id=CHAT_ID, text="✅ Render: бот стартовал и токен работает.")
    print("✅ Сообщение успешно отправлено")
except Exception as e:
    print("❌ Ошибка при отправке сообщения:", e)
