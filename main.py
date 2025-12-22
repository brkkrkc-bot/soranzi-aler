import os
import json
import requests

# ======================
# ENV
# ======================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

SORARE_API = "https://api.sorare.com/graphql"
SEEN_FILE = "seen.json"

# ======================
# PLAYERS (slug : display name)
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
    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": text,
        "disable_web_page_preview": True
    })

def load_seen():
    if not os.path.exists(SEEN_FILE):
        return {}
    try:
        with open(SEEN_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(seen, f)

# ======================
# SORARE API
# ======================
def fetch_cards(slug):
    # LIMITED + Classic/In-Season ayrımı için season alanını da alıyoruz
    query = """
    query PlayerCards($slug: String!) {
      player(slug: $slug) {
        cards(
          rarities: [limited]
          first: 20
          orderBy: PRICE_ASC
        ) {
          nodes {
            id
            slug
            price
            season
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

# ======================
# MAIN
# ======================
def run():
    seen = load_seen()
    send_message("🟢 Sorare NBA LIMITED price checker başladı")

    for slug, name in PLAYERS.items():
        cards = fetch_cards(slug)
        if not cards:
            continue

        # Classic / In-Season ayrı ayrı grupla
        by_season = {}
        for c in cards:
            if c["price"] is None or c["season"] is None:
                continue
            by_season.setdefault(c["season"], []).append(c)

        for season, season_cards in by_season.items():
            # Fiyata göre sırala
            season_cards = sorted(season_cards, key=lambda x: float(x["price"]))
            if len(season_cards) < 2:
                continue

            cheapest = season_cards[0]
            floor = season_cards[1]

            price = float(cheapest["price"])
            floor_price = float(floor["price"])

            card_key = cheapest["id"]  # aynı karta 1 kez alarm

            if price < floor_price and card_key not in seen:
                send_message(
                    f"🔥 UNDER FLOOR LIMITED ({season})\n\n"
                    f"👤 {name}\n"
                    f"💰 New price: {price:.2f} USD\n"
                    f"📉 {season} floor: {floor_price:.2f} USD\n\n"
                    f"🔗 https://sorare.com/nba/cards/{cheapest['slug']}"
                )
                seen[card_key] = True

    save_seen(seen)

# ======================
# ENTRY
# ======================
if __name__ == "__main__":
    run()