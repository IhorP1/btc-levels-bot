import ccxt
import asyncio
from telegram import Bot
from datetime import datetime
import os

# Твои уровни (обновляй при необходимости)
LEVELS = [
    {"type": "Resistance / Liquidity Pool", "price": 98000, "desc": "Upper target + VAH Volume Profile"},
    {"type": "Resistance / Breaker Block", "price": 95000, "desc": "Failed high, sell-side OB, liquidity grabs сверху"},
    {"type": "Resistance", "price": 93000, "desc": "Ключевой уровень отвержения"},
    {"type": "Текущая зона / Equilibrium", "price": 91000, "desc": "Consolidation zone"},
    {"type": "Bullish Order Block / Demand", "price": 88500, "desc": "Buyer defense, unmitigated OB + FVG"},
    {"type": "Support / POC Volume", "price": 86000, "desc": "High volume node (POC weekly), accumulation"},
    {"type": "Deep Support / Liquidity Sweep", "price": 83500, "desc": "Major demand, potential final grab"},
    {"type": "Major Support", "price": 80000, "desc": "Deeper correction target"},
    {"type": "Fib Target ↑", "price": 106000, "desc": "Fib Extension 1.272 — ближайшая цель роста"},
    {"type": "Fib Target ↑", "price": 120000, "desc": "Fib Extension 1.618 — долгосрочная цель"},
]

async def main():
    # Получаем секреты из GitHub
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    CHAT_ID = os.getenv("TELEGRAM_CHANNEL_ID")

    if not TOKEN:
        print("ОШИБКА: TELEGRAM_BOT_TOKEN не найден в секретах!")
        return
    if not CHAT_ID:
        print("ОШИБКА: TELEGRAM_CHANNEL_ID не найден в секретах!")
        return

    print(f"Бот запущен. Chat ID: {CHAT_ID}")

    # Получаем цену BTC
    try:
        exchange = ccxt.binance()
        ticker = exchange.fetch_ticker('BTC/USDT')
        price = ticker['last']
        change = ticker['percentage'] or 0
        print(f"Текущая цена BTC: ${price:,.0f}")
    except Exception as e:
        print(f"Ошибка получения цены: {e}")
        return

    trend = "🟢" if change > 0 else "🔴"
    change_str = f"+{change:.2f}%" if change > 0 else f"{change:.2f}%"

    message = f"""
🚨 <b>BTC/USD — Сигналы по SMC + ICT + Wyckoff</b>

💰 <b>Цена:</b> <code>${price:,.0f}</code> {trend} ({change_str})
📅 {datetime.utcnow().strftime('%d.%m.%Y %H:%M')} UTC

<b>Активные сигналы:</b>
"""

    signal_found = False

    for level in LEVELS:
        lvl_price = level["price"]
        diff_percent = abs(price - lvl_price) / price * 100

        if diff_percent < 1.5:  # близко к уровню
            signal_found = True

            if "Resistance" in level["type"] or "Breaker" in level["type"] or "Liquidity Pool" in level["type"]:
                direction = "🔴 SHORT"
                strength = "🔥 Сильный" if diff_percent < 0.7 else "⚡ Средний"
                sl = int(lvl_price * 1.008)
                tp1 = int(lvl_price * 0.985)
                tp2 = int(lvl_price * 0.97)

            elif "Support" in level["type"] or "Demand" in level["type"] or "Bullish Order Block" in level["type"] or "POC" in level["type"]:
                direction = "🟢 LONG"
                strength = "🔥 Сильный" if diff_percent < 0.7 else "⚡ Средний"
                sl = int(lvl_price * 0.992)
                tp1 = int(lvl_price * 1.015)
                tp2 = int(lvl_price * 1.03)

            else:
                continue

            message += f"\n{direction} <b>{strength}</b>\n"
            message += f"📍 Уровень: <code>${lvl_price:,}</code>\n"
            message += f"<i>{level['desc']}</i>\n"
            message += f"⚡ Entry: ~<code>${price:,.0f}</code>\n"
            message += f"🛑 SL: <code>${sl:,}</code>\n"
            message += f"🎯 TP1: <code>${tp1:,}</code>\n"
            message += f"🎯 TP2: <code>${tp2:,}</code>\n\n"

    if not signal_found:
        message += "\n<i>Нет активных сигналов в данный момент</i>\n"
        message += "<b>Ближайшие уровни:</b>\n"
        sorted_levels = sorted(LEVELS, key=lambda x: abs(price - x["price"]))
        for lvl in sorted_levels[:4]:
            dir_emoji = "⬆️" if lvl["price"] > price else "⬇️"
            prox = "🔥 близко" if abs(price - lvl["price"]) < 2000 else "📍"
            message += f"{dir_emoji} <code>${lvl['price']:,}</code> {prox} — {lvl['desc'][:50]}...\n"

    # Мнение
    if price > 92000:
        opinion = "🟢 Бычий контроль — цель 95–100k"
    elif price > 85000:
        opinion = "⚖️ Консолидация — ждём breakout или sweep"
    else:
        opinion = "🔴 Риск снижения — защита на 83–80k"

    message += f"\n📈 <b>Мнение:</b> {opinion}"
    message += f"\n\n#BTC #Bitcoin #SMC #ICT"

    # Отправка
    bot = Bot(token=TOKEN)
    try:
        await bot.send_message(
            chat_id=CHAT_ID,
            text=message,
            parse_mode='HTML',
            disable_web_page_preview=True
        )
        print("✅ Сообщение успешно отправлено в Telegram!")
    except Exception as e:
        print(f"❌ ОШИБКА ОТПРАВКИ: {str(e)}")
        print("Проверь: бот — админ с правом 'Публиковать сообщения'? Правильный ли chat_id?")

if __name__ == "__main__":
    asyncio.run(main())
