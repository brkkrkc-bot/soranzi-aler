import requests
import json
import os
from datetime import datetime

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

GRAPHQL_URL = "https://api.sorare.com/graphql"

HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0"
}

def send_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": text}, timeout=10)

def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def fetch_market(slug):
    query = """
    query Cards($slug: String!) {
      nbaPlayer(slug: $slug) {
        displayName
        cards(rarities: [limited], onSale: true, first: 20) {
          nodes {
            slug
            season { startYear }
            currentPrice
          }
        }
      }
    }
    """
    r = requests.post(
        GRAPHQL_URL,
        json={"query": query, "variables": {"slug": slug}},
        headers=HEADERS,
        timeout=15
    )
    r.raise_for_status()
    return r.json()["data"]["nbaPlayer"]

def run():
    players = load_json("players.json", {}).get("players", [])
    seen = load_json("seen.json", {})
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    send_message("🟢 Sorare NBA LIMITED price checker başladı")

    for slug in players:
        try:
            data = fetch_market(slug)
            if not data:
                continue

            name = data["displayName"]
            cards = data["cards"]["nodes"]
            prices = [c["currentPrice"] for c in cards if c["currentPrice"]]

            if not prices:
                continue

            floor = min(prices)

            for c in cards:
                key = c["slug"]
                price = c["currentPrice"]
                season = c["season"]["startYear"]
                in_season = season == datetime.now().year

                prev = seen.get(key)
                diff = round(((price - floor) / floor) * 100, 2)

                alert = False
                reason = ""

                if prev is None:
                    alert = True
                    reason = "🆕 Yeni kart"
                elif price < prev:
                    alert = True
                    reason = "📉 Fiyat düştü"

                if alert:
                    tag = "IN-SEASON" if in_season else "CLASSIC"
                    send_message(
                        f"🏀 {name}\n"
                        f"{reason}\n"
                        f"💳 {tag} LIMITED\n"
                        f"💰 ${price:.2f}\n"
                        f"📊 Floor ${floor:.2f}\n"
                        f"📈 %{diff}\n"
                        f"🕒 {now}"
                    )

                seen[key] = price

        except Exception as e:
            print(f"❌ {slug} hata verdi, atlandı: {e}")
            continue

    save_json("seen.json", seen)

if __name__ == "__main__":
    run()