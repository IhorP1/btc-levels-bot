import ccxt
import asyncio
from telegram import Bot
from datetime import datetime
import os  # ← Добавили для чтения переменных окружения

async def send_signal_to_telegram():
    # Получаем токен и ID канала из переменных окружения (секреты GitHub)
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")

    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHANNEL_ID:
        print("Ошибка: Не найдены токен или ID канала в переменных окружения!")
        return

    # Получаем текущую цену BTC
    exchange = ccxt.binance()
    ticker = exchange.fetch_ticker('BTC/USDT')
    current_price = ticker['last']
    change_24h = ticker['percentage']

    trend_emoji = "🟢" if change_24h > 0 else "🔴"
    change_str = f"+{change_24h:.2f}%" if change_24h > 0 else f"{change_24h:.2f}%"

    # Заголовок
    message = f"""
🚨 <b>BTC/USD — Торговый сигнал SMC + ICT + Wyckoff</b>

💰 <b>Текущая цена:</b> <code>${current_price:,.0f}</code> {trend_emoji} ({change_str} за 24ч)
📅 {datetime.now().strftime('%d %B %Y, %H:%M')} (UTC)

<b>Активные сигналы:</b>
"""

    signals_found = False

    # ← Здесь подключи свой levels.py (убедись, что он загружен в репозиторий)
    from levels import LEVELS

    for level in LEVELS:
        price = level["price"]
        type_level = level["type"]
        desc = level["desc"]

        diff = abs(current_price - price)
        percent_diff = (diff / current_price) * 100

        if percent_diff < 1.5:
            signals_found = True

            if "Resistance" in type_level or "Breaker" in type_level or "Liquidity Pool" in type_level:
                direction = "🔴 SHORT"
                entry = current_price
                sl = price + (price * 0.008)
                tp1 = price - (price * 0.015)
                tp2 = price - (price * 0.03)
                strength = "🔥 Сильный" if percent_diff < 0.7 else "⚡ Средний"

            elif "Support" in type_level or "Demand" in type_level or "Bullish Order Block" in type_level or "POC" in type_level:
                direction = "🟢 LONG"
                entry = current_price
                sl = price - (price * 0.008)
                tp1 = price + (price * 0.015)
                tp2 = price + (price * 0.03)
                strength = "🔥 Сильный" if percent_diff < 0.7 else "⚡ Средний"

            elif "Fib Target" in type_level:
                direction = "🎯 Потенциальная цель роста"
                strength = "📈 Долгосрочная"
                entry = sl = tp1 = tp2 = None
            else:
                continue

            message += f"\n{direction} <b>{strength}</b>\n"
            message += f"📍 <b>Уровень:</b> <code>${price:,.0f}</code>\n"
            message += f"<i>{desc}</i>\n"

            if entry:
                message += f"⚡ <b>Entry:</b> ~<code>${entry:,.0f}</code>\n"
                message += f"🛑 <b>SL:</b> <code>${sl:,.0f}</code>\n"
                message += f"🎯 <b>TP1:</b> <code>${tp1:,.0f}</code> (1:2 RR)\n"
                message += f"🎯 <b>TP2:</b> <code>${tp2:,.0f}</code> (1:4 RR)\n"

            message += "⏳ Ждём подтверждения свечой (pin bar / engulfing)\n\n"

    if not signals_found:
        message += "\n<i>📊 Нет активных сигналов сейчас</i>\n"
        message += "<b>Ближайшие уровни для наблюдения:</b>\n"

        sorted_levels = sorted(LEVELS, key=lambda x: abs(current_price - x["price"]))
        for level in sorted_levels[:5]:
            price = level["price"]
            diff = abs(current_price - price)
            proximity = "🔥 Очень близко" if diff < 1000 else "📍 Близко" if diff < 3000 else "⏳ Ждём"
            direction = "⬆️" if price > current_price else "⬇️"
            message += f"\n{direction} <code>${price:,.0f}</code> — {proximity}\n<i>{level['desc']}</i>"

    # Мнение
    if current_price > 92000:
        opinion = "🟢 Бычий сценарий: держимся выше equilibrium. Цель — 95–100k"
    elif 85000 <= current_price <= 92000:
        opinion = "⚖️ Консолидация. Ожидаем sweep ликвидности или breakout"
    else:
        opinion = "🔴 Осторожно: риск теста нижних OB (83–80k)"

    message += f"\n\n📈 <b>Текущее мнение:</b> {opinion}"
    message += f"\n\n#BTC #Bitcoin #SMC #ICT #ТорговыйСигнал"

    # Отправка в Telegram
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    await bot.send_message(
        chat_id=TELEGRAM_CHANNEL_ID,
        text=message,
        parse_mode='HTML',
        disable_web_page_preview=True
    )

    print(f"Сигнал успешно отправлен! Цена: ${current_price:,}")

if __name__ == "__main__":
    asyncio.run(send_signal_to_telegram())
