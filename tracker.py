import os
import requests
from bs4 import BeautifulSoup

# Obtenemos los secretos configurados en GitHub Actions
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Lista de tiendas y productos a rastrear
ITEMS = [
    {
        "name": "Caja Booster TCG (Ejemplo)",
        "url": "https://httpbin.org/html",  # URL de prueba inicial
        "selector": "h1",                   # Elemento HTML donde mirar el texto
        "out_of_stock_text": "agotado"      # Palabra que indica que NO hay stock
    }
]

def send_telegram_alert(message):
    """Envía el mensaje con enlace directo al bot de Telegram."""
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False
    }
    res = requests.post(url, json=payload, timeout=10)
    if res.status_code != 200:
        print(f"Error enviando mensaje a Telegram: {res.text}")

def check_stock():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    for item in ITEMS:
        try:
            response = requests.get(item["url"], headers=headers, timeout=15)
            
            if response.status_code != 200:
                print(f"Error {response.status_code} al entrar a {item['url']}")
                continue

            soup = BeautifulSoup(response.text, "html.parser")
            element = soup.select_one(item["selector"])

            if element:
                status_text = element.get_text().strip().lower()
                print(f"[{item['name']}] Texto encontrado: '{status_text}'")

                # Si el texto de 'agotado' NO está presente, notificamos
                if item["out_of_stock_text"] not in status_text:
                    alert_msg = (
                        f"🚨 *¡HAY STOCK DETECTADO!* 🚨\n\n"
                        f"📦 *Producto:* {item['name']}\n"
                        f"🔗 [Ir a la tienda a comprar]({item['url']})"
                    )
                    send_telegram_alert(alert_msg)
            else:
                print(f"No se encontró el selector '{item['selector']}' en {item['name']}")

        except Exception as e:
            print(f"Fallo revisando {item['name']}: {e}")

if __name__ == "__main__":
    check_stock()
