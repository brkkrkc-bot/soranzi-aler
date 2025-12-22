import os
import json
import requests

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

PLAYERS = [
    "tyrese-maxey",
    "shai-gilgeous-alexander",
    "giannis-antetokounmpo",
    "pascal-siakam",
    "cade-cunningham"
]

SEEN_FILE = "seen.json"

SORARE_API = "https://api.sorare.com/graphql"

QUERY = """
query Market($slug: String!) {
  player(slug: $slug) {
    name
    cards(first: 20, rarities: [limited], orderBy: PRICE_ASC) {
      nodes {
        id
        rarity
        priceUsd
      }
    }
  }
}
"""

def load_seen():
    if not os.path.exists(SEEN_FILE):
        return {}
    with open(SEEN_FILE, "r") as f:
        return json.load(f)

def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(seen, f)

def send_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text})

seen = load_seen()

for slug in PLAYERS:
    res = requests.post(
        SORARE_API,
        json={
            "query": QUERY,
            "variables": {"slug": slug}
        }
    )

    data = res.json()
    cards = data["data"]["player"]["cards"]["nodes"]
    name = data["data"]["player"]["name"]

    if not cards:
        continue

    floor_price = float(cards[0]["priceUsd"])

    for card in cards:
        card_id = card["id"]
        price = float(card["priceUsd"])

        if card_id in seen:
            continue

        if price < floor_price:
            msg = (
                f"🔥 UNDER FLOOR LIMITED!\n"
                f"{name}\n"
                f"💵 Price: ${price:.2f}\n"
                f"📉 Floor: ${floor_price:.2f}"
            )
            send_message(msg)
            seen[card_id] = True

save_seen(seen)
