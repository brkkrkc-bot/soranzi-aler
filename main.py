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
    payload = {"chat_id": CHAT_ID, "text": text}
    requests.post(url, json=payload, timeout=10)

def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def fetch_market(player_slug):
    query = """
    query Cards($slug: String!) {
      nbaPlayer(slug: $slug) {
        displayName
        cards(rarities: [limited], onSale: true, first: 20) {
          nodes {
            slug
            season {
              startYear
            }
            currentPrice
          }
        }
      }
    }
    """
    variables = {"slug": player_slug}
    r = requests.post(
        GRAPHQL_URL,
        json={"query": query, "variables": variables},
        headers=HEADERS,
        timeout=15
    )
    r.raise_for_status()
    return r.json()["data"]["nbaPlayer"]

def run():
    players = load_json("players.json", {})["players"]
    seen = load_json("seen.json", {})
    status = load_json("status.json", {})

    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    send_message("🟢 Sorare NBA LIMITED price checker başladı")

    for slug in players:
        data = fetch_market(slug)
        if not data:
            continue

        name = data["displayName"]
        cards = data["cards"]["nodes"]
        if not cards:
            continue

        prices = [c["currentPrice"] for c in cards if c["currentPrice"]]
        if not prices:
            continue

        floor = min(prices)

        for c in cards:
            card_slug = c["slug"]
            price = c["currentPrice"]
            season = c["season"]["startYear"]
            is_in_season = season == datetime.now().year

            key = f"{card_slug}"

            prev_price = seen.get(key)

            diff_pct = round(((price - floor) / floor) * 100, 2)

            alert = False
            reason = ""

            if key not in seen:
                alert = True
                reason = "🆕 Yeni kart"
            elif price < prev_price:
                alert = True
                reason = "📉 Fiyat düştü"

            if alert:
                season_tag = "IN-SEASON" if is_in_season else "CLASSIC"
                msg = (
                    f"🏀 {name}\n"
                    f"{reason}\n"
                    f"💳 {season_tag} LIMITED\n"
                    f"💰 Fiyat: ${price:.2f}\n"
                    f"📊 Floor: ${floor:.2f}\n"
                    f"📈 Fark: %{diff_pct}\n"
                    f"🕒 {now}"
                )
                send_message(msg)

            seen[key] = price

    save_json("seen.json", seen)
    save_json("status.json", {"last_run": now})

if __name__ == "__main__":
    run()