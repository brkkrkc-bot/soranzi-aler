import os
import json
import requests

# ======================
# ENV
# ======================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# ======================
# PLAYERS (slug : name)
# ======================
PLAYERS = {
    "tyrese-maxey": "Tyrese Maxey",
    "shai-gilgeous-alexander": "Shai Gilgeous-Alexander",
    "giannis-antetokounmpo": "Giannis Antetokounmpo",
    "pascal-siakam": "Pascal Siakam",
    "cade-cunningham": "Cade Cunningham",
}

SEEN_FILE = "seen.json"

# ======================
# HELPERS
# ======================
def send_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text})

def load_seen():
    if not os.path.exists(SEEN_FILE):
        return {}
    with open(SEEN_FILE, "r") as f:
        return json.load(f)

def save_seen(data):
    with open(SEEN_FILE, "w") as f:
        json.dump(data, f)

# ======================
# SORARE API
# ======================
def fetch_cards(slug):
    query = """
    query PlayerCards($slug: String!) {
      player(slug: $slug) {
        cards(rarities: [limited], first: 5) {
          nodes {
            slug
            price
          }
        }
      }
    }
    """

    r = requests.post(
        "https://api.sorare.com/graphql",
        json={"query": query, "variables": {"slug": slug}},
        headers={"Content-Type": "application/json"},
        timeout=20
    )

    data = r.json()

    if "data" not in data or data["data"]["player"] is None:
        return []

    return data["data"]["player"]["cards"]["nodes"]

# ======================
# MAIN LOGIC
# ======================
def run():
    send_message("🟢 Sorare NBA LIMITED price checker başladı (DENEME MODU)")

    seen = load_seen()

    for slug, name in PLAYERS.items():
        cards = fetch_cards(slug)

        if len(cards) < 2:
            continue

        cheapest = cards[0]
        second = cards[1]

        card_id = cheapest["slug"]
        price = cheapest["price"]
        floor = second["price"]

        if price is None or floor is None:
            continue

        # GERÇEK ALARM ŞARTI
        if price < floor and card_id not in seen:
            send_message(
                f"🔥 UNDER FLOOR LIMITED ALERT\n\n"
                f"🏀 {name}\n"
                f"💰 New price: {price} USD\n"
                f"📉 Current floor: {floor} USD\n\n"
                f"🔗 https://sorare.com/nba/cards/{card_id}"
            )

            seen[card_id] = True

    save_seen(seen)

# ======================
# ENTRY
# ======================
if __name__ == "__main__":
    run()