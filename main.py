import os
import json
import time
import requests
from datetime import datetime

# ================== AYARLAR ==================

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

SORARE_API = "https://api.sorare.com/graphql"

PLAYERS = {
    "jaren-jackson-jr": "Jaren Jackson Jr",
    "tyler-herro": "Tyler Herro",
    "jalen-johnson": "Jalen Johnson",
    "jalen-williams": "Jalen Williams",
    "paolo-banchero": "Paolo Banchero",
    "keyonte-george": "Keyonte George",
    "devin-booker": "Devin Booker",
    "matas-buzelis": "Matas Buzelis",
}

SEEN_FILE = "seen.json"

# ================== TELEGRAM ==================

def send_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    r = requests.post(url, json=payload, timeout=15)
    r.raise_for_status()

# ================== DOSYA ==================

def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r") as f:
            return json.load(f)
    return {}

def save_seen(data):
    with open(SEEN_FILE, "w") as f:
        json.dump(data, f, indent=2)

# ================== SORARE ==================

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

    payload = {
        "query": query,
        "variables": {"slug": slug}
    }

    r = requests.post(SORARE_API, json=payload, timeout=20)
    r.raise_for_status()
    data = r.json()

    if "errors" in data:
        return []

    return data["data"]["player"]["cards"]["nodes"]

# ================== ANA LOGIC ==================

def run():
    send_message("🟢 <b>Sorare NBA LIMITED price checker başladı</b>")

    seen = load_seen()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    for slug, name in PLAYERS.items():
        cards = fetch_market(slug)
        if not cards:
            continue

        # in-season ve classic AYRI
        for mode in ["in", "classic"]:
            filtered = []
            for c in cards:
                if mode == "in" and c["inSeasonEligible"]:
                    filtered.append(c)
                if mode == "classic" and not c["inSeasonEligible"]:
                    filtered.append(c)

            if len(filtered) < 1:
                continue

            filtered.sort(key=lambda x: float(x["priceUsd"]))
            floor = float(filtered[0]["priceUsd"])

            for c in filtered:
                card_id = c["slug"]
                price = float(c["priceUsd"])

                key = f"{card_id}"

                if key in seen and seen[key] == price:
                    continue  # spam yok

                diff_pct = ((price - floor) / floor) * 100

                emoji = "🆕" if key not in seen else "📉"

                send_message(
                    f"{emoji} <b>{name}</b>\n"
                    f"🎴 {'IN-SEASON' if mode=='in' else 'CLASSIC'}\n"
                    f"💰 Fiyat: <b>${price:.2f}</b>\n"
                    f"📊 Floor farkı: <b>{diff_pct:+.1f}%</b>\n"
                    f"🔗 https://sorare.com/nba/cards/{card_id}\n"
                    f"🕒 {now}"
                )

                seen[key] = price

    save_seen(seen)

# ================== ÇALIŞTIR ==================

if __name__ == "__main__":
    run()