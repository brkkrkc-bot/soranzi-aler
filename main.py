import os
import json
import requests
from datetime import datetime

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

HEADERS = {
    "Content-Type": "application/json"
}

SORARE_API = "https://api.sorare.com/graphql"

PLAYERS = [
    "Tyler Herro",
    "Jalen Johnson",
    "Jalen Williams",
    "Paolo Banchero",
    "Keyonte George",
    "Devin Booker",
    "Matas Buzelis"
]

SEEN_FILE = "seen.json"


def send_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text
    }
    r = requests.post(url, json=payload, timeout=10)
    r.raise_for_status()


def load_seen():
    if not os.path.exists(SEEN_FILE):
        return {}
    with open(SEEN_FILE, "r") as f:
        return json.load(f)


def save_seen(data):
    with open(SEEN_FILE, "w") as f:
        json.dump(data, f)


def fetch_floor(player_name):
    query = {
        "query": """
        query($name: String!) {
          cards(
            sport: NBA
            rarity: limited
            first: 1
            filter: { playerName: $name }
            sort: PRICE_ASC
          ) {
            nodes {
              slug
              price
            }
          }
        }
        """,
        "variables": {
            "name": player_name
        }
    }

    r = requests.post(SORARE_API, json=query, headers=HEADERS, timeout=15)
    r.raise_for_status()
    data = r.json()

    cards = data.get("data", {}).get("cards", {}).get("nodes", [])
    if not cards:
        return None

    return {
        "slug": cards[0]["slug"],
        "price": float(cards[0]["price"])
    }


def run():
    send_message("🟢 Sorare NBA LIMITED price checker başladı")

    seen = load_seen()
    updated = False

    for player in PLAYERS:
        result = fetch_floor(player)
        if not result:
            continue

        slug = result["slug"]
        price = result["price"]

        last_price = seen.get(player)

        if last_price is None or price < last_price:
            send_message(
                f"🔥 PRICE DROP\n"
                f"👤 {player}\n"
                f"💵 {price} USD\n"
                f"🔗 https://sorare.com/cards/{slug}"
            )
            seen[player] = price
            updated = True

    if updated:
        save_seen(seen)


if __name__ == "__main__":
    run()