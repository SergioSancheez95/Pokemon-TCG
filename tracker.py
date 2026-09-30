import os
import json
import requests
from bs4 import BeautifulSoup

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
DATA_FILE = "seen_products.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "es-ES,es;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
}

def load_previous_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_current_data(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error guardando estado: {e}")

def send_telegram(title, store, url, is_new=False):
    icon = "🆕 *¡NUEVO PRODUCTO DETECTADO!*" if is_new else "🔥 *¡HAY STOCK DISPONIBLE!*"
    msg = (
        f"{icon}\n\n"
        f"🏪 *Tienda:* {store}\n"
        f"📦 *Producto:* {title}\n\n"
        f"🔗 [Ir a la tienda a comprar]({url})"
    )
    url_req = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": msg,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False
    }
    try:
        requests.post(url_req, json=payload, timeout=10)
    except Exception as e:
        print(f"Error enviando mensaje a Telegram: {e}")

def evaluate_item(name, url, store, has_stock, current_state, old_state):
    key = f"{store}::{name}"
    current_state[key] = has_stock

    if key not in old_state:
        print(f"[{store}] Nuevo producto: {name} (Stock: {has_stock})")
        if has_stock:
            send_telegram(name, store, url, is_new=True)
    elif not old_state[key] and has_stock:
        print(f"[{store}] ¡Stock disponible!: {name}")
        send_telegram(name, store, url, is_new=False)
    else:
        print(f"[{store}] Sin cambios: {name}")

def check_mathom(current_state, old_state):
    store = "Mathom"
    url = "https://mathom.es/es/buscar?s=pokemon+30+aniversario"
    try:
        res = requests.get(url, headers=HEADERS, timeout=20)
        if res.status_code != 200:
            return
        soup = BeautifulSoup(res.text, "html.parser")
        items = soup.select(".product-miniature, .js-product-miniature, article.product-item")
        for it in items:
            title_el = it.select_one(".product-title a, h2.product-title a, h3 a")
            if not title_el:
                continue
            name = title_el.get_text().strip()
            link = title_el.get("href", url)
            text = it.get_text().lower()
            no_stock_words = ["avísame", "avisame", "agotado", "fuera de stock", "sin stock"]
            has_stock = not any(w in text for w in no_stock_words)
            evaluate_item(name, link, store, has_stock, current_state, old_state)
    except Exception as e:
        print(f"Error en {store}: {e}")

def check_woocommerce(store, url, current_state, old_state):
    try:
        res = requests.get(url, headers=HEADERS, timeout=20)
        if res.status_code != 200:
            return
        soup = BeautifulSoup(res.text, "html.parser")
        items = soup.select("li.product, .type-product, .wc-block-grid__product")
        for it in items:
            title_el = it.select_one(".woocommerce-loop-product__title, h2, h3, .wc-block-grid__product-title")
            link_el = it.select_one("a.woocommerce-LoopProduct-link, a")
            if not title_el or not link_el:
                continue
            name = title_el.get_text().strip()
            link = link_el.get("href", url)
            text = it.get_text().lower()
            no_stock_words = ["agotado", "out of stock", "sin existencias", "leer más"]
            has_stock = not any(w in text for w in no_stock_words)
            evaluate_item(name, link, store, has_stock, current_state, old_state)
    except Exception as e:
        print(f"Error en {store}: {e}")

def check_shinyhit_single(current_state, old_state):
    store = "ShinyHit"
    url = "https://shinyhit.com/producto/celebracion-30-aniversario-coleccion-premium-ditto/"
    try:
        res = requests.get(url, headers=HEADERS, timeout=20)
        if res.status_code != 200:
            return
        soup = BeautifulSoup(res.text, "html.parser")
        name_el = soup.select_one("h1.product_title, h1")
        name = name_el.get_text().strip() if name_el else "Celebración 30 Aniversario Ditto"
        text = soup.get_text().lower()
        no_stock_words = ["agotado", "out of stock", "reservas agotadas", "sin existencias"]
        cart_btn = soup.select_one("button[name='add-to-cart'], .single_add_to_cart_button")
        has_stock = bool(cart_btn) and not any(w in text for w in no_stock_words)
        evaluate_item(name, url, store, has_stock, current_state, old_state)
    except Exception as e:
        print(f"Error en {store}: {e}")

def main():
    old_state = load_previous_data()
    current_state = {}

    print("--- INICIANDO RASTREO MULTITIENDA ---")

    # TEST DE PRUEBA REAL:
    evaluate_item("Caja Sobres 30 Aniversario (TEST PRUEBA)", "https://pokealhambra.com/shop/", "PokeAlhambra", True, current_state, {})

    check_mathom(current_state, old_state)
    check_woocommerce("PokeAlhambra", "https://pokealhambra.com/shop/", current_state, old_state)
    check_woocommerce("Mundo Distorsión", "https://mundodistorsion.es/product-category/30-aniversario/", current_state, old_state)
    check_shinyhit_single(current_state, old_state)

    old_state.update(current_state)
    save_current_data(old_state)

if __name__ == "__main__":
    main()
    old_state.update(current_state)
    save_current_data(old_state)
