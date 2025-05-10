import os
import requests
import time
import asyncio
from telegram import Bot

# На Render переменные окружения задаются вручную, dotenv не нужен
# from dotenv import load_dotenv
# load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
COINGLASS_API_KEY = os.getenv("COINGLASS_API_KEY")

bot = Bot(token=TELEGRAM_TOKEN)

sent_signals = {}  # словарь: symbol -> timestamp последней отправки
SIGNAL_REPEAT_INTERVAL = 600  # 10 минут

async def send_signal(symbol, oi_change, volume):
    print(f"Отправка сигнала для {symbol}...")
    msg = (
        f"📈 Сигнал по {symbol}!",
        f"\nOI рост: {oi_change}%",
        f"\nОбъем: {volume:,}$"
    )
    await asyncio.to_thread(bot.send_message, chat_id=CHAT_ID, text=''.join(msg))
    sent_signals[symbol] = time.time()

def get_filtered_signals():
    url = "https://api.coinglass.com/api/futures?volume_increase=true&open_interest_increase=true&price_drop_limit=3"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {COINGLASS_API_KEY}"
    }

    try:
        r = requests.get(url, headers=headers)
        print(f"🔍 Запрос фильтрованных сигналов: HTTP {r.status_code}")

        if r.status_code != 200:
            print(f"❌ Ошибка ответа: {r.status_code} — {r.text}")
            return []

        data = r.json().get('data', [])
        return data

    except Exception as e:
        print(f"‼️ Ошибка при запросе фильтрованных сигналов: {e}")
        return []

async def monitor():
    print("🚀 Запуск monitor()")
    print("▶️ Начинаем мониторинг...")
    print("TELEGRAM_TOKEN exists:", bool(TELEGRAM_TOKEN))
    print("CHAT_ID:", CHAT_ID)
    print("COINGLASS_API_KEY exists:", bool(COINGLASS_API_KEY))

    await asyncio.to_thread(bot.send_message, chat_id=CHAT_ID, text="✅ Бот запущен (фильтр CoinGlass)")

    while True:
        signals = get_filtered_signals()

        if not signals:
            print("⏳ Нет подходящих сигналов на данный момент.")
        else:
            current_time = time.time()
            for s in signals:
                try:
                    symbol = s.get('symbol')
                    oi_change = s.get('oiChangePercent', 0)
                    volume = s.get('volumeUsd', 0)

                    if volume >= 1_000_000 and oi_change > 5:
                        last_sent = sent_signals.get(symbol, 0)
                        if current_time - last_sent >= SIGNAL_REPEAT_INTERVAL:
                            await send_signal(symbol, oi_change, volume)
                            await asyncio.sleep(1)
                        else:
                            print(f"🔁 {symbol} уже отправлен недавно — повтор через {int(SIGNAL_REPEAT_INTERVAL - (current_time - last_sent))}с")
                    else:
                        print(f"🔸 Пропуск {symbol}: объем или OI не соответствуют порогу.")
                except Exception as e:
                    print(f"‼️ Ошибка при обработке сигнала: {e}")

        await asyncio.sleep(600)

if __name__ == '__main__':
    print("🟢 main.py стартует...")
    try:
        asyncio.run(monitor())
    except Exception as e:
        print(f"‼️ Ошибка запуска: {e}")
