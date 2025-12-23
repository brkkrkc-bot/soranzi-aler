import os
import requests
import json
from datetime import datetime

API = "https://api.sorare.com/graphql"

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

PLAYERS = {
    "jaren-jackson-jr": "Jaren Jackson Jr",
    "tyler-herro": "Tyler Herro",
    "jalen-williams": "Jalen Williams",
    "paolo-banchero": "Paolo Banchero",
}

STATE_FILE = "seen.json"


def send(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    r = requests.post(url, json={"chat_id": CHAT_ID, "text": msg}, timeout=10)
    r.raise_for_status()


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {}


def save_state(s):
    with open(STATE_FILE, "w") as f:
        json.dump(s, f, indent=2)


def fetch_market(slug):
    query = """
    query PlayerCards($slug: String!) {
      basketballPlayers(slugs: [$slug]) {
        nodes {
          cards(
            first: 20,
            rarities: [limited],
            seasons: [IN_SEASON],
            onSale: true
          ) {
            nodes {
              id
              serialNumber
              price
            }
          }
        }
      }
    }
    """

    r = requests.post(
        API,
        json={"query": query, "variables": {"slug": slug}},
        headers={"Content-Type": "application/json"},
        timeout=15,
    )
    r.raise_for_status()

    players = r.json()["data"]["basketballPlayers"]["nodes"]
    if not players:
        return []

    return players[0]["cards"]["nodes"]


def run():
    state = load_state()
    now = datetime.now().strftime("%H:%M")

    for slug, name in PLAYERS.items():
        cards = fetch_market(slug)
        if not cards:
            continue

        prices = [float(c["price"]) for c in cards]
        floor = min(prices)

        for c in cards:
            card_id = c["id"]
            price = float(c["price"])
            last = state.get(card_id)

            diff = ((price - floor) / floor) * 100

            if last is None or price < last:
                send(
                    f"🆕 {name} (IN-SEASON)\n"
                    f"💰 ${price:.2f}\n"
                    f"📊 Floor farkı: {diff:+.1f}%\n"
                    f"🔢 Serial: {c['serialNumber']}\n"
                    f"🕒 {now}"
                )
                state[card_id] = price

    save_state(state)


if __name__ == "__main__":
    send("🟢 Sorare NBA LIMITED price checker başladı")
    run()