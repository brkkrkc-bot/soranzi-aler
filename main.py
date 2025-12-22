import os
import json
import requests
from pathlib import Path

# ================== AYARLAR ==================

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

GRAPHQL_URL = "https://api.sorare.com/graphql"

SEEN_FILE = "seen.json"

PLAYERS = {
    "pascal-siakam": "Pascal Siakam",
    "tyrese-maxey": "Tyrese Maxey",
    "shai-gilgeous-alexander": "Shai Gilgeous-Alexander",
    "giannis-antetokounmpo": "Giannis Antetokounmpo",
    "cade-cunningham": "Cade Cunningham",
}

# ================== TELEGRAM ==================

def send_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "disable_web_page_preview": True
    }
    r = requests.post(url, json=payload, timeout=10)
    r.raise_for_status()

# ================== SEEN ==================

def load_seen():
    if not Path(SEEN_FILE).exists():
        return {}
    with open(SEEN_FILE, "r") as f:
        return json.load(f)

def save_seen(data):
    with open(SEEN_FILE, "w") as f:
        json.dump(data, f)

# ================== SORARE ==================

QUERY = """
query Cards($slug: String!) {
  player(slug: $slug) {
    cards(first: 20, rarities: [limited], onSale: true, orderBy: PRICE_ASC) {
      nodes {
        slug
        price
        season {
          startYear
        }
      }
    }
  }
}
"""

def fetch_cards(slug):
    r = requests.post(
        GRAPHQL_URL,
        json={"query": QUERY, "variables": {"slug": slug}},
        headers={"Content-Type": "application/json"},
        timeout=20
    )
    data = r.json()
    if "data" not in data or data["data"]["player"] is None:
        return []

    return data["data"]["player"]["cards"]["nodes"]

# ================== MAIN ==================

def run():
    send_message("🟢 Sorare NBA LIMITED price checker başladı")

    seen = load_seen()
    updated = False

    for slug, name in PLAYERS.items():
        cards = fetch_cards(slug)
        if not cards:
            continue

        # season bazlı ayır
        groups = {}
        for c in cards:
            season = c["season"]["startYear"]
            groups.setdefault(season, []).append(c)

        for season, items in groups.items():
            if len(items) < 2:
                continue

            cheapest = items[0]
            second = items[1]

            if cheapest["price"] < second["price"]:
                card_id = cheapest["slug"]

                if card_id in seen:
                    continue  # spam yok

                msg = (
                    "🔥 UNDER FLOOR LIMITED ALERT\n\n"
                    f"👤 {name}\n"
                    f"📅 Season: {season}\n"
                    f"💰 New price: {cheapest['price']} USD\n"
                    f"📉 Floor: {second['price']} USD\n"
                    f"🔗 https://sorare.com/nba/cards/{card_id}"
                )

                send_message(msg)
                seen[card_id] = True
                updated = True

    if updated:
        save_seen(seen)

# ================== ENTRY ==================

if __name__ == "__main__":
    run()