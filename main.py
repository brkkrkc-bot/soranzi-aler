import os
import requests

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

PLAYERS = {
    "tyrese-maxey": "Tyrese Maxey",
    "shai-gilgeous-alexander": "Shai Gilgeous-Alexander",
    "giannis-antetokounmpo": "Giannis Antetokounmpo",
    "pascal-siakam": "Pascal Siakam",
    "cade-cunningham": "Cade Cunningham",
}

SORARE_API = "https://api.sorare.com/graphql"

def send_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text})

def fetch_cards(slug):
    query = """
    query PlayerCards($slug: String!) {
      player(slug: $slug) {
        cards(rarities: [limited], first: 20, orderBy: PRICE_ASC) {
          nodes {
            id
            slug
            rarity
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
        print(f"❌ API error for {slug}: {data}")
        return []

    return data["data"]["player"]["cards"]["nodes"]

def run():
    send_message("🟢 Sorare NBA LIMITED price checker başladı")

    for slug, name in PLAYERS.items():
        cards = fetch_cards(slug)

        if len(cards) < 2:
            continue

        cheapest = cards[0]
        second = cards[1]

        if cheapest["price"] < second["]()
