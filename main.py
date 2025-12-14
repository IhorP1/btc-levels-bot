import ccxt
import asyncio
from telegram import Bot
from datetime import datetime
import config  # твой файл с токенами
from levels import LEVELS

async def send_levels_to_telegram():
    # Получаем текущую цену BTC
    exchange = ccxt.binance()
    ticker = exchange.fetch_ticker('BTC/USDT')
    current_price = ticker['last']
    change_24h = ticker['percentage']

    # Формируем эмодзи для измененания
    trend_emoji = "🟢" if change_24h > 0 else "🔴"
    change_str = f"+{change_24h:.2f}%" if change_24h > 0 else f"{change_24h:.2f}%"

    # Заголовок
    message = f"""
🚨 <b>BTC/USD — Анализ уровней SMC + ICT + Wyckoff</b>

💰 <b>Текущая цена:</b> <code>${current_price:,.0f}</code> {trend_emoji} ({change_str} за 24ч)
📅 {datetime.now().strftime('%d %B %Y, %H:%M')} (UTC)

<b>Ключевые уровни:</b>
"""

    # Добавляем уровни с оценкой близости
    for level in LEVELS:
        price = level["price"]
        diff = abs(current_price - price)
        proximity = "🔥 БЛИЗКО!" if diff < 1000 else "📍 Средне" if diff < 3000 else "⏳ Далеко"

        if price > current_price:
            direction = "⬆️ Сопротивление"
        elif price < current_price:
            direction = "⬇️ Поддержка / Цель"
        else:
            direction = "🎯 ТОЧНО НА УРОВНЕ!"

        message += f"\n{direction} <code>${price:,.0f}</code> — {proximity}\n<i>{level['desc']}</i>"

    # Добавляем мнение (можно автоматизировать дальше, пока — по логике цены)
    if current_price > 92000:
        opinion = "🟢 <b>Бычий контроль</b> — держимся выше ключевых OB. Ожидаю тест 95–98k при объёмах."
    elif 87000 <= current_price <= 92000:
        opinion = "⚖️ <b>Консолидация / Re-accumulation</b> — классическая фаза Wyckoff C. Ждём sweep или breakout."
    elif current_price < 87000:
        opinion = "🔴 <b>Медвежий риск</b> — пробой POC. Возможен sweep к 83–80k перед разворотом."
    else:
        opinion = "📊 Нейтрально — наблюдаем за реакцией на ближайшие уровни."

    message += f"\n\n📈 <b>Текущее мнение:</b>\n{opinion}"
    message += f"\n\n#BTC #Bitcoin #SMC #ICT"

    # Отправляем в Telegram
    bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
    await bot.send_message(
        chat_id=config.TELEGRAM_CHANNEL_ID,
        text=message,
        parse_mode='HTML',
        disable_web_page_preview=True
    )

    print(f"Сообщение успешно отправлено! Цена: ${current_price}")

# Запуск
if __name__ == "__main__":
    asyncio.run(send_levels_to_telegram())
