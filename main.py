import requests
import os
import json

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

GRAPHQL_URL = "https://api.sorare.com/graphql"
STATE_FILE = "state.json"

PLAYERS = {
    "jaren-jackson-jr": "Jaren Jackson Jr",
}

HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0"
}


def send(msg):
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": msg},
        timeout=10
    )


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
      nbaCards(
        first: 50
        filter: {
          playerSlugs: [$slug]
          rarities: [limited]
          onSale: true
        }
      ) {
        nodes {
          slug
          season {
            startYear
          }
          liveSingleSaleOffer {
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
    return r.json()["data"]["nbaCards"]["nodes"]


def run():
    state = load_state()
    send("🟢 Sorare NBA LIMITED checker başladı")

    for slug, name in PLAYERS.items():
        cards = fetch_market(slug)

        for season_type in ["in-season", "classic"]:
            filtered = []

            for c in cards:
                price = c["liveSingleSaleOffer"]["price"]
                year = c["season"]["startYear"]

                if season_type == "in-season" and year == 2024:
                    filtered.append((c, price))
                if season_type == "classic" and year != 2024:
                    filtered.append((c, price))

            if not filtered:
                continue

            floor = min(p for _, p in filtered)

            for c, price in filtered:
                key = c["slug"]
                old = state.get(key)

                if old == price:
                    continue

                diff = ((price - floor) / floor) * 100
                emoji = "🟢" if diff <= 0 else "🔴"

                send(
                    f"{emoji} {name}\n"
                    f"{season_type.upper()}\n"
                    f"💰 {price:.2f}$\n"
                    f"📊 Floor farkı: {diff:+.1f}%"
                )

                state[key] = price

    save_state(state)


if __name__ == "__main__":
    run()