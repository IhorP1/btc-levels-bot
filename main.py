import os
import requests
from telegram import Bot

# Токен и группа из Secrets (обязательно!)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not TELEGRAM_TOKEN or not CHAT_ID:
    print("ОШИБКА: Добавь TELEGRAM_TOKEN и CHAT_ID в Secrets!")
    exit(1)

bot = Bot(token=TELEGRAM_TOKEN)

def send(text):
    try:
        bot.send_message(chat_id=CHAT_ID, text=text, disable_web_page_preview=True)
        print("Сообщение отправлено!")
    except Exception as e:
        print(f"Ошибка отправки: {e}")

def get_btc_levels():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true&include_24hr_vol=true"
        data = requests.get(url, timeout=10).json()["bitcoin"]
        price = data["usd"]
        change = data["usd_24h_change"]
        volume = data["usd_24h_vol"]

        support = round(price * 0.97)
        resistance = round(price * 1.06)
        poc = round(price)
        fvg = f"{round(price * 0.985)} — {round(price * 1.015)}"

        signal = f"""
УРОВНИ BTC — ОБНОВЛЕНО

Цена: ${price:,.0f}
Изменение 24ч: {change:+.2f}%
Объём: ${volume:,.1f}B

• Поддержка: ${support:,.0f}
• Сопротивление: ${resistance:,.0f}
• POC: ${poc:,.0f}
• FVG зона: {fvg}$

Grok: {'LONG bias — ждём отскок' if change > -1 else 'Осторожно — возможен пробой вниз'}
"""
        send(signal)
    except Exception as e:
        send(f"Ошибка данных: {e}")

# При запуске — сразу отправляем уровни
print("Бот запущен — отправляю текущие уровни BTC...")
get_btc_levels()

# Больше ничего — GitHub Actions сам перезапустит через час (по cron)
