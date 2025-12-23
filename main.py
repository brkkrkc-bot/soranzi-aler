import requests
import os
import json
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
    requests.post(url, json={"chat_id": CHAT_ID, "text": text}, timeout=20)

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
    query NBAPlayerCards($slug: String!) {
      nbaPlayer(slug: $slug) {
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

    if not data.get("data") or not data["data"].get("nbaPlayer"):
        return []

    return data["data"]["nbaPlayer"]["cards"]["nodes"]

def run():
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    send_message("🟢 Sorare NBA LIMITED price checker başladı")

    state = load_state()
    sent = False

    for slug, name in PLAYERS.items():
        cards = fetch_market(slug)
        in_season = [c for c in cards if c["inSeasonEligible"] and c["priceUsd"]]

        if not in_season:
            continue

        in_season.sort(key=lambda x: x["priceUsd"])
        floor = round(in_season[0]["priceUsd"], 2)

        for c in in_season:
            cid = c["slug"]
            price = round(c["priceUsd"], 2)
            old = state.get(cid)

            diff_pct = round(((price - floor) / floor) * 100, 1)

            if old is None:
                send_message(
                    f"🆕 YENİ IN-SEASON KART\n"
                    f"{name}\n"
                    f"Serial #{c['serialNumber']}\n"
                    f"Fiyat: ${price}\n"
                    f"Floor: ${floor}\n"
                    f"Fark: {diff_pct:+}%"
                )
                state[cid] = price
                sent = True

            elif price < old:
                drop = round(((price - old) / old) * 100, 1)
                send_message(
                    f"🔻 FİYAT DÜŞTÜ\n"
                    f"{name}\n"
                    f"Serial #{c['serialNumber']}\n"
                    f"{old}$ → {price}$ ({drop}%)\n"
                    f"Floor farkı: {diff_pct:+}%"
                )
                state[cid] = price
                sent = True

    if not sent:
        send_message(
            f"✅ Sorare NBA checker aktif\n"
            f"{now}\n"
            f"📊 Yeni kart / fiyat düşüşü yok"
        )

    save_state(state)

if __name__ == "__main__":
    run()