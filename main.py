import os
import json
import requests
from datetime import datetime

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

SORARE_API = "https://api.sorare.com/graphql"

PERCENT_DROP_ALERT = 5  # %5

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
    payload = {"chat_id": CHAT_ID, "text": text}
    requests.post(url, json=payload, timeout=10)


def load_seen():
    if not os.path.exists(SEEN_FILE):
        return {}
    with open(SEEN_FILE, "r") as f:
        return json.load(f)


def save_seen(data):
    with open(SEEN_FILE, "w") as f:
        json.dump(data, f, indent=2)


def fetch_floor(player_name, season_type):
    query = {
        "query": """
        query($name: String!, $season: CardSeason!) {
          cards(
            sport: NBA
            rarity: limited
            season: $season
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
            "name": player_name,
            "season": season_type
        }
    }

    r = requests.post(SORARE_API, json=query, timeout=15)
    cards = r.json().get("data", {}).get("cards", {}).get("nodes", [])

    if not cards:
        return None

    return {
        "slug": cards[0]["slug"],
        "price": float(cards[0]["price"])
    }


def run():
    today = datetime.utcnow().strftime("%Y-%m-%d")

    seen = load_seen()
    alerts_sent_today = False

    for player in PLAYERS:
        for season, label in [("CLASSIC", "Classic"), ("IN_SEASON", "In-Season")]:
            result = fetch_floor(player, season)
            if not result:
                continue

            key = f"{player}_{label}"
            new_price = result["price"]
            slug = result["slug"]

            old_price = seen.get(key)

            if old_price:
                drop_percent = ((old_price - new_price) / old_price) * 100
            else:
                drop_percent = 0

            if old_price and drop_percent >= PERCENT_DROP_ALERT:
                send_message(
                    f"🔥 %{drop_percent:.1f} DROP\n"
                    f"👤 {player}\n"
                    f"🎴 {label}\n"
                    f"💵 {new_price} USD (önce {old_price})\n"
                    f"🔗 https://sorare.com/cards/{slug}"
                )
                alerts_sent_today = True
                seen[key] = new_price

            elif old_price is None:
                seen[key] = new_price

    # 🔔 GÜNLÜK STATUS
    if seen.get("_last_status_date") != today and not alerts_sent_today:
        send_message(
            f"✅ Sorare NBA checker aktif\n"
            f"📅 {today}\n"
            f"📊 Bugün floor altı kart yok"
        )
        seen["_last_status_date"] = today

    save_seen(seen)


if __name__ == "__main__":
    run()