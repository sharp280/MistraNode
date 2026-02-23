from datetime import datetime

def format_crypto_response(name, data):
    """
    Перетворює сирі дані в технічний звіт терміналу (БЕЗ СІРОГО КОЛЬОРУ).
    """
    if not data:
        return f"ERROR: DataFetchFailed. TARGET: {name.upper()}. STATUS: 404."
    
    trend = "[UP]" if data['change_24h'] >= 0 else "[DOWN]"
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Використовуємо символи, які не перетворюють текст на цитату
    return (
        f"**Запит:** {name.upper()}/USD\n"
        f"┣ Ціна: **${data['price']:,.2f}**\n"
        f"┣ Тренд: {trend}\n"
        f"┣ Зміна (24h): {data['change_24h']}%\n"
        f"┗ **Timestamp:** {current_time} | СТАТУС: REAL_TIME"
    )

def format_terminal_greeting(user_nick):
    return f"**>> ВІТАННЯ, {user_nick}. МОДУЛЬ АКТИВОВАНО. ОЧІКУЮ ЗАПИТ.**"