import requests

def get_coin_price(coin_id="bitcoin"):
    """
    Отримує ціну криптовалюти та зміну за 24г через CoinGecko Public API.
    """
    try:
        # Формуємо URL для запиту
        url = f"https://api.coingecko.com/api/v3/simple/price"
        params = {
            "ids": coin_id,
            "vs_currencies": "usd",
            "include_24hr_change": "true"
        }
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if coin_id in data:
            return {
                "price": data[coin_id]['usd'],
                "change_24h": round(data[coin_id]['usd_24h_change'], 2)
            }
        return None
    except Exception as e:
        print(f"[*] Crypto API Error: {e}")
        return None