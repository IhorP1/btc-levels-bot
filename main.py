import os
import logging
import time
import sys
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from telegram import Bot
from telegram.error import TelegramError

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# Токен и группа из Secrets (обязательно!)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not TELEGRAM_TOKEN or not CHAT_ID:
    logger.error("ОШИБКА: Добавь TELEGRAM_TOKEN и CHAT_ID в окружение/Secrets!")
    sys.exit(1)

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
    sys.exit(1)
except Exception as e:
    logger.exception("Неожиданная ошибка при getMe: %s", e)
    sys.exit(1)

def create_session_with_retries(total_retries=3, backoff_factor=0.3, status_forcelist=(500, 502, 503, 504)):
    session = requests.Session()
    retries = Retry(total=total_retries, backoff_factor=backoff_factor, status_forcelist=status_forcelist, allowed_methods=frozenset(['GET', 'POST']))
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session

def send(text):
    try:
        bot.send_message(chat_id=chat_id_cast, text=text, disable_web_page_preview=True)
        logger.info("Сообщение отправлено!")
    except TelegramError as e:
        logger.exception("Ошибка отправки (TelegramError): %s", e)
    except Exception as e:
        logger.exception("Ошибка отправки (прочее): %s", e)

def get_btc_levels(session=None):
    session = session or create_session_with_retries()
    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            "ids": "bitcoin",
            "vs_currencies": "usd",
            "include_24hr_change": "true",
            "include_24hr_vol": "true"
        }
        resp = session.get(url, params=params, timeout=10)
        resp.raise_for_status()
        resp_json = resp.json()
        data = resp_json.get("bitcoin")
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

        # Форматируем объём: если очень большой, показываем в миллиардах/миллионах
        vol_text = f"${volume:,.0f}"
        try:
            if volume >= 1_000_000_000:
                vol_text = f"${volume/1_000_000_000:,.2f}B"
            elif volume >= 1_000_000:
                vol_text = f"${volume/1_000_000:,.2f}M"
        except Exception:
            vol_text = f"${volume}"

        # Решение Grok (упрощённо)
        try:
            change_val = float(change)
        except Exception:
            change_val = 0.0

        grok = "LONG bias — ждём отскок" if change_val > -1 else "Осторожно — возможен пробой вниз"

        signal = (
            "УРОВНИ BTC — ОБНОВЛЕНО\n\n"
            f"Цена: ${price:,.0f}\n"
            f"Изменение 24ч: {change_val:+.2f}%\n"
            f"Объём: {vol_text}\n\n"
            f"• Поддержка: ${support:,.0f}\n"
            f"• Сопротивление: ${resistance:,.0f}\n"
            f"• POC: ${poc:,.0f}\n"
            f"• FVG зона: {fvg}\n\n"
            f"Grok: {grok}"
        )
        send(signal)
        return True
    except Exception as e:
        logger.exception("Ошибка получения или обработки данных: %s", e)
        # Попробуем отправить сообщение об ошибке (если бот валиден)
        try:
            send(f"Ошибка данных: {e}")
        except Exception:
            logger.error("Не удалось отправить сообщение об ошибке.")
        return False

def main():
    # INTERVAL_SECONDS: если задан — скрипт будет работать в цикле с паузой INTERVAL_SECONDS
    interval = os.getenv("INTERVAL_SECONDS")
    session = create_session_with_retries()
    if interval:
        try:
            interval_sec = int(interval)
            if interval_sec <= 0:
                raise ValueError("INTERVAL_SECONDS должен быть положительным")
        except Exception as e:
            logger.error("Неверный INTERVAL_SECONDS: %s. Скрипт завершится.", e)
            sys.exit(1)

        logger.info("Бот запущен в режиме демона. Интервал: %s секунд", interval_sec)
        while True:
            logger.info("Отправляю текущие уровни BTC...")
            get_btc_levels(session=session)
            logger.info("Жду %s секунд до следующего запуска...", interval_sec)
            time.sleep(interval_sec)
    else:
        logger.info("Бот запущен — отправляю текущие уровни BTC (однократно)...")
        get_btc_levels(session=session)

if __name__ == "__main__":
    main()
