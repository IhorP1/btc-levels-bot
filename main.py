# ... (всё остальное то же самое)

    # Отправка в Telegram с обработкой ошибок
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    try:
        await bot.send_message(
            chat_id=TELEGRAM_CHANNEL_ID,
            text=message,
            parse_mode='HTML',
            disable_web_page_preview=True
        )
        print("Сообщение успешно отправлено в Telegram!")
    except Exception as e:
        print(f"ОШИБКА ОТПРАВКИ В TELEGRAM: {e}")
        print(f"Тип ошибки: {type(e).__name__}")
        # Это выведет точную ошибку в логи GitHub Actions

    print(f"Скрипт завершён. Цена BTC: ${current_price:,}")
