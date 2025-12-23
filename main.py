import os
import json
import requests

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
    r = requests.post(url, json=payload, timeout=10)
    r.raise_for_status()


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
    r.raise_for_status()
    cards = r.json().get("data", {}).get("cards", {}).get("nodes", [])

    if not cards:
        return None

    return {
        "slug": cards[0]["slug"],
        "price": float(cards[0]["price"])
    }


def run():
    send_message("🟢 Sorare NBA LIMITED price checker başladı")

    seen = load_seen()
    changed = False

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

            if old_price is None or drop_percent >= PERCENT_DROP_ALERT:
                if old_price:
                    msg = (
                        f"🔥 %{drop_percent:.1f} DROP\n"
                        f"👤 {player}\n"
                        f"🎴 {label}\n"
                        f"💵 {new_price} USD (önce {old_price})\n"
                        f"🔗 https://sorare.com/cards/{slug}"
                    )
                else:
                    msg = (
                        f"🆕 FIRST FLOOR\n"
                        f"👤 {player}\n"
                        f"🎴 {label}\n"
                        f"💵 {new_price} USD\n"
                        f"🔗 https://sorare.com/cards/{slug}"
                    )

                send_message(msg)
                seen[key] = new_price
                changed = True

    if changed:
        save_seen(seen)


if __name__ == "__main__":
    run()