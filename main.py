import os
import json
import requests
from datetime import datetime, timezone, timedelta

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

SORARE_API = "https://api.sorare.com/graphql"
SEEN_FILE = "seen.json"
STATUS_FILE = "status.json"

# ======================
# PLAYERS
# ======================
PLAYERS = {
    "tyrese-maxey": "Tyrese Maxey",
    "shai-gilgeous-alexander": "Shai Gilgeous-Alexander",
    "giannis-antetokounmpo": "Giannis Antetokounmpo",
    "pascal-siakam": "Pascal Siakam",
    "cade-cunningham": "Cade Cunningham",
    "tyler-herro": "Tyler Herro",
    "jalen-johnson": "Jalen Johnson",
    "jalen-williams": "Jalen Williams",
    "paolo-banchero": "Paolo Banchero",
    "keyonte-george": "Keyonte George",
    "devin-booker": "Devin Booker",
    "matas-buzelis": "Matas Buzelis",
}

# ======================
# HELPERS
# ======================
def send_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text})

def load_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r") as f:
            return json.load(f)
    except:
        return default

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f)

# ======================
# TELEGRAM STATUS CHECK
# ======================
def check_status_command():
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    r = requests.get(url, timeout=10).json()

    if "result" not in r:
        return

    for update in r["result"]:
        msg = update.get("message", {})
        text = msg.get("text", "")
        chat_id = msg.get("chat", {}).get("id")

        if text == "/status" and chat_id == int(CHAT_ID):
            status = load_json(STATUS_FILE, {})
            send_message(
                "📊 Sorare NBA Sniper Status\n\n"
                f"🕒 Last scan: {status.get('last_scan', 'N/A')} (TR)\n"
                f"⏱ Scan interval: 5 minutes\n"
                f"👥 Players tracked: {len(PLAYERS)}\n"
                f"🔔 Alerts: LIMITED only"
            )

# ======================
# SORARE API
# ======================
QUERY = """
query PlayerCards($slug: String!) {
  player(slug: $slug) {
    cards(rarities: [limited], sport: NBA, first: 20) {
      nodes {
        slug
        season
        inSeasonEligible
        liveSingleSaleOffer {
          price {
            amount
            currency
          }
        }
      }
    }
  }
}
"""

def fetch_cards(slug):
    r = requests.post(
        SORARE_API,
        json={"query": QUERY, "variables": {"slug": slug}},
        headers={"Content-Type": "application/json"},
        timeout=20
    )
    data = r.json()
    if "data" not in data or data["data"]["player"] is None:
        return []
    return data["data"]["player"]["cards"]["nodes"]

# ======================
# MAIN
# ======================
def run():
    seen = set(load_json(SEEN_FILE, []))
    check_status_command()

    now_tr = datetime.now(timezone.utc) + timedelta(hours=3)
    save_json(STATUS_FILE, {
        "last_scan": now_tr.strftime("%H:%M")
    })

    for slug, name in PLAYERS.items():
        cards = fetch_cards(slug)

        listings = []
        for c in cards:
            offer = c.get("liveSingleSaleOffer")
            if not offer:
                continue
            if offer["price"]["currency"] != "USD":
                continue

            listings.append({
                "slug": c["slug"],
                "price": float(offer["price"]["amount"]),
                "in_season": c["inSeasonEligible"]
            })

        for season_type in [True, False]:
            group = [c for c in listings if c["in_season"] == season_type]
            if len(group) < 2:
                continue

            group.sort(key=lambda x: x["price"])
            cheapest, floor = group[0], group[1]

            if cheapest["price"] < floor["price"] and cheapest["slug"] not in seen:
                send_message(
                    "🔥 UNDER FLOOR LIMITED ALERT\n\n"
                    f"👤 {name}\n"
                    f"🏷 {'In-Season' if season_type else 'Classic'}\n"
                    f"💰 New price: {cheapest['price']} USD\n"
                    f"📉 Floor: {floor['price']} USD\n"
                    f"🔗 https://sorare.com/nba/cards/{cheapest['slug']}"
                )
                seen.add(cheapest["slug"])

    save_json(SEEN_FILE, list(seen))

# ======================
if __name__ == "__main__":
    run()