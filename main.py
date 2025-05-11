import os
import requests
import time
import asyncio
from telegram import Bot
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
COINGLASS_API_KEY = os.getenv("COINGLASS_API_KEY")

bot = Bot(token=TELEGRAM_TOKEN)

async def send_signal(symbol, prev_oi, curr_oi):
    print(f"Отправка сигнала для {symbol}...")
    msg = (
        f"\ud83d\udcc8 Сигнал по {symbol}!",
        f"\nРост OI: {curr_oi / prev_oi * 100 - 100:.2f}%"
    )
    await asyncio.to_thread(bot.send_message, chat_id=CHAT_ID, text=''.join(msg))

def get_open_interest(symbol):
    url = f'https://open-api.coinglass.com/public/v1/oi?symbol={symbol}'
    headers = {'Authorization': f'Bearer {COINGLASS_API_KEY}'}

    try:
        print(f"\ud83d\udd0d Запрос OI к CoinGlass: {url}")
        r = requests.get(url, headers=headers)
        print(f"\ud83d\udce9 HTTP статус: {r.status_code}")

        if r.status_code != 200:
            print(f"\u274c Ошибка запроса: {r.status_code}, ответ: {r.text}")
            return 0, 0

        data = r.json().get('data', [])
        if not data:
            print("\u26a0\ufe0f Ответ CoinGlass пустой или не содержит 'data'")
            return 0, 0

        oi_data = data[0]
        prev_oi = oi_data.get('prevOI', 0)
        curr_oi = oi_data.get('currOI', 0)
        print(f"\u2705 OI получен: prevOI={prev_oi}, currOI={curr_oi}")
        return prev_oi, curr_oi

    except Exception as e:
        print(f"\u203c\ufe0f Исключение при запросе OI для {symbol}: {e}")
        return 0, 0

def get_volume_price(symbol):
    url = f'https://open-api.coinglass.com/public/v1/futures_volume_chart?symbol={symbol}&time_type=1h'
    headers = {'Authorization': f'Bearer {COINGLASS_API_KEY}'}
    try:
        r = requests.get(url, headers=headers)
        if r.status_code != 200:
            print(f"\u274c Ошибка получения объема/цены для {symbol}: {r.status_code}")
            return [], []
        data = r.json().get('data', {})
        vol_list = data.get('volList', [])
        price_list = data.get('priceList', [])
        print(f"\ud83d\udcc8 Объемов: {len(vol_list)}, цен: {len(price_list)}")
        return vol_list, price_list
    except Exception as e:
        print(f"\u203c\ufe0f Ошибка получения объема/цены для {symbol}: {e}")
        return [], []

async def monitor():
    print("\ud83d\ude80 Запуск monitor()")
    print("\u25b6\ufe0f Начинаем мониторинг...")
    print("TELEGRAM_TOKEN exists:", bool(TELEGRAM_TOKEN))
    print("CHAT_ID:", CHAT_ID)
    print("COINGLASS_API_KEY exists:", bool(COINGLASS_API_KEY))

    await asyncio.to_thread(bot.send_message, chat_id=CHAT_ID, text="\u2705 Бот запущен (только CoinGlass)")

    # ВРЕМЕННО фиксированный список символов, пока CoinGlass /symbol не работает
    symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "DOGEUSDT", "OPUSDT", "ARBUSDT", "LINKUSDT"]

    while True:
        for symbol in symbols:
            try:
                prev_oi, curr_oi = get_open_interest(symbol)
                vol_list, price_list = get_volume_price(symbol)

                if len(vol_list) < 2 or len(price_list) < 2:
                    print(f"\u26a0\ufe0f Недостаточно данных для анализа {symbol}")
                    continue

                volume_now = vol_list[-1].get('value', 0)
                volume_prev = vol_list[-2].get('value', 0)
                price_now = price_list[-1].get('value', 0)
                price_prev = price_list[-2].get('value', 0)

                volume_rising = volume_now >= 1_000_000
                oi_growing = curr_oi > prev_oi * 1.05
                volume_not_falling = volume_now >= volume_prev * 0.9
                price_stable = abs(price_now - price_prev) / price_prev < 0.03  # менее 3% изменения

                if oi_growing and volume_rising and volume_not_falling and price_stable:
                    await send_signal(symbol, prev_oi, curr_oi)
                    await asyncio.sleep(1)
                else:
                    print(f"\u23f3 {symbol}: условия не выполнены.")
            except Exception as e:
                print(f"Ошибка с {symbol}: {e}")
        await asyncio.sleep(600)

if __name__ == '__main__':
    asyncio.run(monitor())
