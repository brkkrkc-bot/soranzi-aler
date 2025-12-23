import requests
import os
import json
from datetime import datetime

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

GRAPHQL_URL = "https://api.sorare.com/graphql"

PLAYERS = {
    "jaren-jackson-jr": "Jaren Jackson Jr",
    # buraya istediğin oyuncuyu ekle
}

HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0"
}

STATE_FILE = "state.json"


def send(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": msg})


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


def fetch_market(slug):
    query = """
    query Market($slug: String!) {
      nbaPlayer(slug: $slug) {
        name
        cards(rarities: [limited], first: 50) {
          nodes {
            slug
            season
            onSale
            price
          }
        }
      }
    }
    """
    r = requests.post(
        GRAPHQL_URL,
        headers=HEADERS,
        json={"query": query, "variables": {"slug": slug}},
        timeout=20
    )
    r.raise_for_status()
    return r.json()["data"]["nbaPlayer"]["cards"]["nodes"]


def run():
    state = load_state()
    today = datetime.now().strftime("%Y-%m-%d")

    send("🟢 Sorare NBA LIMITED checker başladı")

    for slug, name in PLAYERS.items():
        cards = fetch_market(slug)

        for season_type in ["in-season", "classic"]:
            filtered = [
                c for c in cards
                if c["onSale"]
                and ((season_type == "in-season" and c["season"] == "2024")
                     or (season_type == "classic" and c["season"] != "2024"))
            ]

            if not filtered:
                continue

            floor = min(c["price"] for c in filtered)

            for c in filtered:
                key = f"{slug}-{c['slug']}"
                old_price = state.get(key)

                if old_price is not None and old_price == c["price"]:
                    continue

                diff = ((c["price"] - floor) / floor) * 100
                emoji = "🟢" if diff <= 0 else "🔴"

                send(
                    f"{emoji} {name}\n"
                    f"{season_type.upper()}\n"
                    f"💰 {c['price']:.2f}$\n"
                    f"📊 Floor farkı: {diff:+.1f}%"
                )

                state[key] = c["price"]

    save_state(state)


if __name__ == "__main__":
    run()