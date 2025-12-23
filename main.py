import os
import json
import requests
from datetime import datetime

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

SORARE_API = "https://api.sorare.com/graphql"
SEEN_FILE = "seen.json"

PLAYERS = {
    "jaren-jackson-jr": "Jaren Jackson Jr",
    "tyler-herro": "Tyler Herro",
    "jalen-johnson": "Jalen Johnson",
    "jalen-williams": "Jalen Williams",
    "paolo-banchero": "Paolo Banchero",
    "keyonte-george": "Keyonte George",
    "devin-booker": "Devin Booker",
    "matas-buzelis": "Matas Buzelis"
}

def send_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": text}, timeout=15)

def load_seen():
    if not os.path.exists(SEEN_FILE):
        return {"sales": {}}
    with open(SEEN_FILE, "r") as f:
        return json.load(f)

def save_seen(data):
    with open(SEEN_FILE, "w") as f:
        json.dump(data, f, indent=2)

def fetch_inseason_sales(slug):
    query = """
    query($slug: String!) {
      player(slug: $slug) {
        cards(
          rarities: [limited]
          onSale: true
          first: 10
        ) {
          nodes {
            slug
            price
            isInSeason
            sale {
              id
            }
          }
        }
      }
    }
    """
    r = requests.post(
        SORARE_API,
        json={"query": query, "variables": {"slug": slug}},
        timeout=20
    )
    data = r.json()
    if not data.get("data") or not data["data"]["player"]:
        return []
    return data["data"]["player"]["cards"]["nodes"]

def run():
    seen = load_seen()

    for slug, name in PLAYERS.items():
        cards = fetch_inseason_sales(slug)

        for card in cards:
            if not card["isInSeason"]:
                continue

            sale = card.get("sale")
            if not sale:
                continue

            sale_id = sale["id"]

            # 🔑 ASIL NOKTA: yeni SATIŞ İLANI
            if sale_id in seen["sales"]:
                continue

            send_message(
                f"🆕 YENİ IN-SEASON SATIŞ İLANI\n\n"
                f"👤 {name}\n"
                f"💰 {card['price']} USD\n\n"
                f"https://sorare.com/nba/cards/{card['slug']}"
            )

            seen["sales"][sale_id] = {
                "player": name,
                "price": card["price"],
                "time": datetime.utcnow().isoformat()
            }

    save_seen(seen)

if __name__ == "__main__":
    run()