import os
import json
import requests
from datetime import datetime

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0"
}

GRAPHQL_URL = "https://api.sorare.com/graphql"

SEEN_FILE = "seen.json"
STATUS_FILE = "status.json"
PLAYERS_FILE = "players.json"

# ------------------ UTILS ------------------

def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def send_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text}
    requests.post(url, json=payload, timeout=10)

# ------------------ SORARE ------------------

def fetch_market(slug):
    query = {
        "query": """
        query Market($slug: String!) {
          nbaCards(
            first: 25
            rarity: limited
            season: IN_SEASON
            playerSlug: $slug
            orderBy: PRICE_ASC
          ) {
            nodes {
              id
              price
              slug
            }
          }
        }
        """,
        "variables": {"slug": slug}
    }

    r = requests.post(GRAPHQL_URL, headers=HEADERS, json=query, timeout=15)
    r.raise_for_status()
    return r.json()["data"]["nbaCards"]["nodes"]

# ------------------ MAIN ------------------

def run():
    seen = load_json(SEEN_FILE, {})
    status = load_json(STATUS_FILE, {})
    players = load_json(PLAYERS_FILE, [])

    today = datetime.utcnow().strftime("%Y-%m-%d")

    if status.get("started") != today:
        send_message("🟢 Sorare NBA LIMITED price checker başladı")
        status["started"] = today
        save_json(STATUS_FILE, status)

    for player in players:
        slug = player["slug"]
        name = player["name"]

        try:
            cards = fetch_market(slug)
        except Exception:
            continue

        if not cards:
            continue

        floor_price = float(cards[0]["price"])

        for card in cards:
            listing_id = card["id"]
            price = float(card["price"])

            if listing_id not in seen:
                diff = ((price - floor_price) / floor_price) * 100
                emoji = "🟢" if diff <= 0 else "🔴"

                msg = (
                    f"{emoji} {name} (IN-SEASON)\n"
                    f"💰 {price:.2f} $\n"
                    f"📉 Floor: {floor_price:.2f} $\n"
                    f"📊 Fark: {diff:+.1f}%"
                )

                send_message(msg)
                seen[listing_id] = price

            else:
                old_price = seen[listing_id]
                if price < old_price:
                    diff = ((price - floor_price) / floor_price) * 100

                    msg = (
                        f"🔻 {name} (IN-SEASON)\n"
                        f"⬇️ Fiyat düştü\n"
                        f"💰 {old_price:.2f} → {price:.2f} $\n"
                        f"📊 Fark: {diff:+.1f}%"
                    )

                    send_message(msg)
                    seen[listing_id] = price

    save_json(SEEN_FILE, seen)

# ------------------

if __name__ == "__main__":
    run()
