import os
import json
import time
import requests

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

SEEN_FILE = "seen.json"

PLAYERS = [
    "Tyler Herro",
    "Jalen Johnson",
    "Jalen Williams",
    "Paolo Banchero",
    "Keyonte George",
    "Devin Booker",
    "Matas Buzelis",
    "Jaren Jackson Jr."
]

SORARE_API = "https://api.sorare.com/graphql"


def send_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    r = requests.post(url, json={"chat_id": CHAT_ID, "text": text})
    r.raise_for_status()


def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r") as f:
            return json.load(f)
    return {}


def save_seen(data):
    with open(SEEN_FILE, "w") as f:
        json.dump(data, f, indent=2)


def fetch_market(player):
    query = {
        "query": """
        query Market($name: String!) {
          nbaCards(
            first: 50
            rarities: [limited]
            playerName: $name
            onSale: true
          ) {
            nodes {
              slug
              season
              sale {
                id
                price {
                  usd
                }
              }
            }
          }
        }
        """,
        "variables": {"name": player},
    }

    r = requests.post(SORARE_API, json=query)
    r.raise_for_status()
    return r.json()["data"]["nbaCards"]["nodes"]


def run():
    send_message("🟢 Sorare NBA LIMITED price checker başladı")

    seen = load_seen()
    updated = False

    for player in PLAYERS:
        cards = fetch_market(player)

        grouped = {"in_season": [], "classic": []}

        for c in cards:
            if not c["sale"]:
                continue

            price = float(c["sale"]["price"]["usd"])
            season = "in_season" if c["season"] == "IN_SEASON" else "classic"

            grouped[season].append({
                "sale_id": c["sale"]["id"],
                "price": price,
                "slug": c["slug"]
            })

        for season, items in grouped.items():
            if not items:
                continue

            floor = min(i["price"] for i in items)

            for item in items:
                sid = item["sale_id"]
                price = item["price"]

                diff_pct = ((price - floor) / floor) * 100

                # YENİ KART
                if sid not in seen:
                    msg = (
                        f"🆕 Yeni kart listelendi\n"
                        f"👤 {player}\n"
                        f"🟡 {'In-Season' if season=='in_season' else 'Classic'} LIMITED\n"
                        f"💰 ${price:.2f}\n"
                        f"📊 Floor: ${floor:.2f}\n"
                        f"{'📉' if diff_pct < 0 else '📈'} "
                        f"Floor’a göre %{diff_pct:.1f}"
                    )
                    send_message(msg)

                    seen[sid] = {
                        "price": price,
                        "player": player,
                        "season": season
                    }
                    updated = True
                    continue

                # AYNI KART – FİYAT DÜŞÜŞÜ
                old_price = seen[sid]["price"]
                if price < old_price:
                    change = ((price - old_price) / old_price) * 100
                    msg = (
                        f"🔻 Fiyat düştü\n"
                        f"👤 {player}\n"
                        f"🟡 {'In-Season' if season=='in_season' else 'Classic'} LIMITED\n"
                        f"💰 ${old_price:.2f} → ${price:.2f}\n"
                        f"📉 Değişim: %{change:.1f}\n"
                        f"📊 Güncel floor: ${floor:.2f}"
                    )
                    send_message(msg)

                    seen[sid]["price"] = price
                    updated = True

    if updated:
        save_seen(seen)


if __name__ == "__main__":
    run()