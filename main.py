import os
import requests
import json
from datetime import datetime

# ================== CONFIG ==================
SORARE_API = "https://api.sorare.com/graphql"
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

PLAYERS = {
    "jaren-jackson-jr": "Jaren Jackson Jr",
    "tyler-herro": "Tyler Herro",
    "jalen-williams": "Jalen Williams",
    "paolo-banchero": "Paolo Banchero",
}

STATE_FILE = "seen.json"
# ============================================


def send_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text}
    r = requests.post(url, json=payload, timeout=10)
    r.raise_for_status()


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def fetch_market(player_slug):
    query = """
    query Market($slug: String!) {
      basketballPlayer(slug: $slug) {
        cards(rarities: [limited], seasons: [IN_SEASON], first: 20) {
          nodes {
            slug
            serialNumber
            season
            liveSingleSaleOffer {
              price
            }
          }
        }
      }
    }
    """

    variables = {"slug": player_slug}

    r = requests.post(
        SORARE_API,
        json={"query": query, "variables": variables},
        headers={"Content-Type": "application/json"},
        timeout=15,
    )
    r.raise_for_status()
    data = r.json()

    return data["data"]["basketballPlayer"]["cards"]["nodes"]


def run():
    state = load_state()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    for slug, name in PLAYERS.items():
        cards = fetch_market(slug)

        prices = [
            float(c["liveSingleSaleOffer"]["price"])
            for c in cards
            if c["liveSingleSaleOffer"]
        ]

        if not prices:
            continue

        floor = min(prices)

        for c in cards:
            offer = c["liveSingleSaleOffer"]
            if not offer:
                continue

            price = float(offer["price"])
            card_id = c["slug"]

            last_price = state.get(card_id)
            diff_pct = ((price - floor) / floor) * 100

            # 🔔 YENİ KART veya FİYAT DEĞİŞİMİ
            if last_price is None or price < last_price:
                msg = (
                    f"🆕 {name} (IN-SEASON)\n"
                    f"💰 Fiyat: ${price:.2f}\n"
                    f"📉 Floor farkı: {diff_pct:+.1f}%\n"
                    f"🔢 Serial: {c['serialNumber']}\n"
                    f"🕒 {now}"
                )
                send_message(msg)
                state[card_id] = price

    save_state(state)


if __name__ == "__main__":
    send_message("🟢 Sorare NBA LIMITED price checker başladı")
    run()