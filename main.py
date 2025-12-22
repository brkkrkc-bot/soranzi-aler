import os
import json
import requests
from datetime import datetime

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

SEEN_FILE = "seen.json"

SORARE_API = "https://api.sorare.com/graphql"

PLAYERS = {
    "tyrese-maxey": "Tyrese Maxey",
    "shai-gilgeous-alexander": "Shai Gilgeous-Alexander",
    "giannis-antetokounmpo": "Giannis Antetokounmpo",
    "pascal-siakam": "Pascal Siakam",
    "cade-cunningham": "Cade Cunningham",
    "tyler-herro": "Tyler Herro",
    "jalen-johnson": "Jalen Johnson",
    "jalen-williams": "Jalen Williams",
    "paolo-banchero": "Paolo Banchero",
    "keyonte-george": "Keyonte George",
    "devin-booker": "Devin Booker",
    "matas-buzelis": "Matas Buzelis"
}

QUERY = """
query PlayerCards($slug: String!) {
  player(slug: $slug) {
    cards(rarities: [limited], sport: NBA, first: 20) {
      nodes {
        slug
        season
        inSeasonEligible
        liveSingleSaleOffer {
          price {
            amount
            currency
          }
        }
      }
    }
  }
}
"""

def send_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text})

def load_seen():
    if not os.path.exists(SEEN_FILE):
        return set()
    with open(SEEN_FILE, "r") as f:
        return set(json.load(f))

def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen), f)

def fetch_cards(slug):
    r = requests.post(
        SORARE_API,
        json={"query": QUERY, "variables": {"slug": slug}},
        headers={"Content-Type": "application/json"},
        timeout=20
    )
    data = r.json()
    if "data" not in data or data["data"]["player"] is None:
        return []
    return data["data"]["player"]["cards"]["nodes"]

def run():
    seen = load_seen()

    send_message("🟢 Sorare NBA LIMITED price checker başladı")

    for slug, name in PLAYERS.items():
        cards = fetch_cards(slug)

        listings = []
        for c in cards:
            offer = c.get("liveSingleSaleOffer")
            if not offer:
                continue
            if offer["price"]["currency"] != "USD":
                continue

            listings.append({
                "slug": c["slug"],
                "price": float(offer["price"]["amount"]),
                "in_season": c["inSeasonEligible"]
            })

        # Classic ve In-Season AYRI
        for season_type in [True, False]:
            filtered = [c for c in listings if c["in_season"] == season_type]

            if len(filtered) < 2:
                continue

            filtered.sort(key=lambda x: x["price"])

            cheapest = filtered[0]
            floor = filtered[1]

            print(f"[DEBUG] {name} | {'IN-SEASON' if season_type else 'CLASSIC'} | "
                  f"{cheapest['price']} vs {floor['price']}")

            if cheapest["price"] < floor["price"]:
                if cheapest["slug"] in seen:
                    continue

                seen.add(cheapest["slug"])
                save_seen(seen)

                send_message(
                    "🔥 UNDER FLOOR LIMITED ALERT\n\n"
                    f"👤 {name}\n"
                    f"🏷 {'In-Season' if season_type else 'Classic'}\n"
                    f"💰 New price: {cheapest['price']} USD\n"
                    f"📊 Floor: {floor['price']} USD\n"
                    f"🔗 https://sorare.com/nba/cards/{cheapest['slug']}"
                )

if __name__ == "__main__":
    run()