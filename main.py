import requests
import json
import os

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

SORARE_API = "https://api.sorare.com/graphql"

PLAYERS = {
    "pascal-siakam": "Pascal Siakam",
    "tyler-herro": "Tyler Herro",
    "jalen-johnson": "Jalen Johnson",
    "jalen-williams": "Jalen Williams",
    "paolo-banchero": "Paolo Banchero",
    "keyonte-george": "Keyonte George",
    "devin-booker": "Devin Booker",
    "matas-buzelis": "Matas Buzelis"
}

SEEN_FILE = "seen.json"


def load_seen():
    if not os.path.exists(SEEN_FILE):
        return {}
    with open(SEEN_FILE, "r") as f:
        return json.load(f)


def save_seen(data):
    with open(SEEN_FILE, "w") as f:
        json.dump(data, f, indent=2)


def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    requests.post(url, json=payload, timeout=10)


def fetch_cards(slug):
    query = """
    query ($slug: String!) {
      player(slug: $slug) {
        cards(first: 5, rarities: [limited], orderBy: PRICE_ASC) {
          nodes {
            slug
            price
          }
        }
      }
    }
    """
    r = requests.post(
        SORARE_API,
        json={"query": query, "variables": {"slug": slug}},
        headers={"Content-Type": "application/json"},
        timeout=20
    )

    data = r.json()
    if "data" not in data or data["data"]["player"] is None:
        return []

    return data["data"]["player"]["cards"]["nodes"]


def run():
    send_message("🟢 Sorare NBA LIMITED price checker başladı (DEBUG MODE)")

    seen = load_seen()

    for slug, name in PLAYERS.items():
        cards = fetch_cards(slug)

        if len(cards) < 2:
            continue

        cheapest = cards[0]
        second = cards[1]

        if cheapest["price"] is None or second["price"] is None:
            continue

        # ANA ALERT ŞARTI
        if cheapest["price"] < second["price"]:
            card_id = cheapest["slug"]

            if card_id in seen:
                continue

            msg = (
                f"🔥 <b>LIMITED FLOOR ALERT</b>\n\n"
                f"🏀 {name}\n"
                f"💰 New price: {cheapest['price']} USD\n"
                f"📊 Current floor: {second['price']} USD\n\n"
                f"🔗 https://sorare.com/nba/cards/{card_id}"
            )

            send_message(msg)
            seen[card_id] = True

    save_seen(seen)


if __name__ == "__main__":
    run()