import os
import requests
import json

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# İzlenecek oyuncular (LIMITED)
PLAYERS = {
    "tyrese-maxey": "Tyrese Maxey",
    "shai-gilgeous-alexander": "Shai Gilgeous-Alexander",
    "giannis-antetokounmpo": "Giannis Antetokounmpo",
    "pascal-siakam": "Pascal Siakam",
    "cade-cunningham": "Cade Cunningham"
}

SORARE_API = "https://api.sorare.com/graphql"


def send_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": text,
        "disable_web_page_preview": True
    })


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
        SORARE_API,
        json={"query": query, "variables": {"slug": slug}},
        headers={"Content-Type": "application/json"},
        timeout=20
    )

    data = r.json()

    if "data" not in data or data["data"]["player"] is None:
        print(f"API error for {slug}: {data}")
        return []

    return data["data"]["player"]["cards"]["nodes"]


def run():
    send_message("🟢 Sorare NBA LIMITED price checker başladı (DENEME MODU)")

    for slug, name in PLAYERS.items():
        cards = fetch_cards(slug)

        if len(cards) < 2:
            continue

        cheapest = cards[0]
        second = cards[1]

        # 🔥 DENEME İÇİN BİLEREK EŞİT / ALT KABUL EDİYORUZ
        if cheapest["price"] <= second["price"]:
            send_message(
                f"🔥 UNDER FLOOR LIMITED ALERT (TEST)\n\n"
                f"👤 {name}\n"
                f"💰 New price: {cheapest['price']} USD\n"
                f"📉 Current floor: {second['price']} USD\n\n"
                f"🔗 https://sorare.com/nba/cards/{cheapest['slug']}"
            )


if __name__ == "__main__":
    run()