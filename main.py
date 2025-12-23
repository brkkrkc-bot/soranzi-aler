import requests
import os
import json
import time
from datetime import datetime

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

SORARE_API = "https://api.sorare.com/graphql"

STATE_FILE = "state.json"

PLAYERS = {
    "jaren-jackson-jr": "Jaren Jackson Jr",
    "tyler-herro": "Tyler Herro",
    "jalen-williams": "Jalen Williams",
    "paolo-banchero": "Paolo Banchero",
    "devin-booker": "Devin Booker",
    "jalen-johnson": "Jalen Johnson",
    "keyonte-george": "Keyonte George"
}

def send_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text}
    r = requests.post(url, json=payload, timeout=20)
    r.raise_for_status()

def load_state():
    if not os.path.exists(STATE_FILE):
        return {}
    with open(STATE_FILE, "r") as f:
        return json.load(f)

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

def fetch_market(slug):
    query = """
    query PlayerCards($slug: String!) {
      player(slug: $slug) {
        cards(rarities: [limited], onSale: true, first: 50) {
          nodes {
            slug
            serialNumber
            season
            inSeasonEligible
            priceUsd
          }
        }
      }
    }
    """

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0"
    }

    payload = {
        "query": query,
        "variables": {"slug": slug}
    }

    r = requests.post(SORARE_API, json=payload, headers=headers, timeout=20)
    r.raise_for_status()
    data = r.json()

    if "errors" in data or data["data"]["player"] is None:
        return []

    return data["data"]["player"]["cards"]["nodes"]

def run():
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    send_message("🟢 Sorare NBA LIMITED price checker başladı")

    state = load_state()
    something_sent = False

    for slug, name in PLAYERS.items():
        cards = fetch_market(slug)
        in_season = [c for c in cards if c["inSeasonEligible"] and c["priceUsd"]]

        if not in_season:
            continue

        in_season.sort(key=lambda x: x["priceUsd"])
        floor = in_season[0]["priceUsd"]

        for c in in_season:
            card_id = c["slug"]
            price = round(c["priceUsd"], 2)

            old_price = state.get(card_id)

            diff_pct = round(((price - floor) / floor) * 100, 1)

            # 🆕 yeni kart
            if old_price is None:
                msg = (
                    f"🆕 YENİ IN-SEASON KART\n"
                    f"{name}\n"
                    f"Serial: #{c['serialNumber']}\n"
                    f"Fiyat: ${price}\n"
                    f"Floor: ${floor}\n"
                    f"Fark: {diff_pct:+}%"
                )
                send_message(msg)
                state[card_id] = price
                something_sent = True

            # 🔻 fiyat düşüşü
            elif price < old_price:
                drop_pct = round(((price - old_price) / old_price) * 100, 1)
                msg = (
                    f"🔻 FİYAT DÜŞTÜ\n"
                    f"{name}\n"
                    f"Serial: #{c['serialNumber']}\n"
                    f"Eski: ${old_price}\n"
                    f"Yeni: ${price} ({drop_pct}%)\n"
                    f"Floor: ${floor}\n"
                    f"Floor farkı: {diff_pct:+}%"
                )
                send_message(msg)
                state[card_id] = price
                something_sent = True

    if not something_sent:
        send_message(
            f"✅ Sorare NBA checker aktif\n"
            f"{now}\n"
            f"📊 Bugün floor altı / yeni kart yok"
        )

    save_state(state)

if __name__ == "__main__":
    run()