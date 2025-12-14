import os
import logging
import requests
from telegram import Bot
from telegram.error import TelegramError

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# Токен и группа из Secrets (обязательно!)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not TELEGRAM_TOKEN or not CHAT_ID:
    logger.error("ОШИБКА: Добавь TELEGRAM_TOKEN и CHAT_ID в Secrets!")
    exit(1)

# Показываем минимальную проверку — длину токена и сам CHAT_ID (не выводим сам токен)
logger.info("TELEGRAM_TOKEN задан (length=%d). CHAT_ID=%s", len(TELEGRAM_TOKEN), CHAT_ID)

# Попробуем привести CHAT_ID к int, если это возможно (Telegram API принимает и строку)
try:
    chat_id_cast = int(CHAT_ID)
except Exception:
    chat_id_cast = CHAT_ID

bot = Bot(token=TELEGRAM_TOKEN)

# Проверим валидность токена и получим данные бота
try:
    me = bot.get_me()
    logger.info("Бот валиден: %s (id=%s)", me.username if hasattr(me, "username") else me, getattr(me, "id", ""))
except TelegramError as e:
    logger.exception("Не удалось запросить getMe — проверь TELEGRAM_TOKEN: %s", e)
    exit(1)
except Exception as e:
    logger.exception("Неожиданная ошибка при getMe: %s", e)
    exit(1)

def send(text):
    try:
        bot.send_message(chat_id=chat_id_cast, text=text, disable_web_page_preview=True)
        logger.info("Сообщение отправлено!")
    except TelegramError as e:
        logger.exception("Ошибка отправки (TelegramError): %s", e)
    except Exception as e:
        logger.exception("Ошибка отправки (прочее): %s", e)

def get_btc_levels():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true&include_24hr_vol=true"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json().get("bitcoin")
        if not data:
            raise ValueError("Нет ключа 'bitcoin' в ответе API")

        price = data.get("usd")
        change = data.get("usd_24h_change")
        volume = data.get("usd_24h_vol")

        if price is None or change is None or volume is None:
            raise ValueError(f"Неполные данные от API: price={price}, change={change}, volume={volume}")

        # Приводим значения
        support = round(price * 0.97)
        resistance = round(price * 1.06)
        poc = round(price)
        fvg = f"{round(price * 0.985)} — {round(price * 1.015)}"

        # Форматируем объём: если очень большой, показываем в миллиардах
        vol_text = f"${volume:,.0f}"
        try:
            if volume >= 1_000_000_000:
                vol_text = f"${volume/1_000_000_000:,.2f}B"
            elif volume >= 1_000_000:
                vol_text = f"${volume/1_000_000:,.2f}M"
        except Exception:
            vol_text = f"${volume}"

        signal = f"""
УРОВНИ BTC — ОБНОВЛЕНО

Цена: ${price:,.0f}
Изменение 24ч: {change:+.2f}%
Объём: {vol_text}

• Поддержка: ${support:,.0f}
• Сопротивление: ${resistance:,.0f}
• POC: ${poc:,.0f}
• FVG зона: {fvg}

Grok: {"LONG bias — ждём отскок" if change > -1 else "Осторожно — возможен пробой вниз"}
"""
        send(signal)
    except Exception as e:
        logger.exception("Ошибка получения или обработки данных: %s", e)
        # Попробуем отправить сообщение об ошибке (если бот валиден)
        try:
            send(f"Ошибка данных: {e}")
        except Exception:
            logger.error("Не удалось отправить сообщение об ошибке.")

# При запуске — сразу отправляем уровни
logger.info("Бот запущен — отправляю текущие уровни BTC...")
get_btc_levels()

# Больше ничего — GitHub Actions сам перезапустит через час (по cron)
