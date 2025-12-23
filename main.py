import os
import json
import time
import requests

# ================== AYARLAR ==================

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

SORARE_API = "https://api.sorare.com/graphql"

SEEN_FILE = "seen.json"

PERCENT_ALERT = 15  # % fark alerti
CHECK_ONLY_IN_SEASON_NEW_CARD = True

PLAYERS = {
    "jaren-jackson-jr": "Jaren Jackson Jr",
    "tyler-herro": "Tyler Herro",
    "jalen-johnson": "Jalen Johnson",
    "jalen-williams": "Jalen Williams",
    "paolo-banchero": "Paolo Banchero",
    "keyonte-george": "Keyonte George",
    "devin-booker": "Devin Booker",
    "matas-buzelis": "Matas Buzelis"
}

# ================== YARDIMCI ==================

def load_seen():
    if not os.path.exists(SEEN_FILE):
        return {"price": {}, "new_card": {}}
    with open(SEEN_FILE, "r") as f:
        return json.load(f)

def save_seen(data):
    with open(SEEN_FILE, "w") as f:
        json.dump(data, f, indent=2)

def send_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text}
    r = requests.post(url, data=payload, timeout=10)
    r.raise_for_status()

# ================== SORARE ==================

def fetch_cards(slug):
    query = """
    query PlayerCards($slug: String!) {
      player(slug: $slug) {
        cards(first: 20, rarities: [limited], onSale: true) {
          nodes {
            slug
            price
            season
            rarity
            isInSeason
          }
        }
      }
    }
    """
    r = requests.post(
        SORARE_API,
        json={"query": query, "variables": {"slug": slug}},
        timeout=20
    )
    data = r.json()
    if "data" not in data or not data["data"]["player"]:
        return []
    return data["data"]["player"]["cards"]["nodes"]

# ================== ANA ==================

def run():
    send_message("🟢 Sorare NBA LIMITED price checker başladı")

    seen = load_seen()

    for slug, name in PLAYERS.items():
        cards = fetch_cards(slug)
        if len(cards) < 2:
            continue

        cards = sorted(cards, key=lambda x: float(x["price"]))
        cheapest = cards[0]
        second = cards[1]

        # ===== 1️⃣ YENİ IN-SEASON KART BİLDİRİMİ =====
        if cheapest["isInSeason"]:
            card_id = cheapest["slug"]
            if card_id not in seen["new_card"]:
                send_message(
                    f"🆕 YENİ IN-SEASON KART\n\n"
                    f"👤 {name}\n"
                    f"💰 {cheapest['price']} USD\n\n"
                    f"https://sorare.com/nba/cards/{card_id}"
                )
                seen["new_card"][card_id] = True

        # ===== 2️⃣ FLOOR ALTINA DÜŞME =====
        if cheapest["price"] < second["price"]:
            key = cheapest["slug"]
            if key not in seen["price"]:
                diff = ((second["price"] - cheapest["price"]) / second["price"]) * 100
                send_message(
                    f"🔥 FİYAT DÜŞÜŞÜ\n\n"
                    f"👤 {name}\n"
                    f"💰 Yeni: {cheapest['price']} USD\n"
                    f"📉 Floor: {second['price']} USD\n"
                    f"📊 Fark: %{diff:.1f}\n\n"
                    f"https://sorare.com/nba/cards/{key}"
                )
                seen["price"][key] = True

        # ===== 3️⃣ % FARK ALERT =====
        diff_percent = ((second["price"] - cheapest["price"]) / second["price"]) * 100
        if diff_percent >= PERCENT_ALERT:
            key = cheapest["slug"] + "_percent"
            if key not in seen["price"]:
                send_message(
                    f"⚡ % FARK ALERT\n\n"
                    f"👤 {name}\n"
                    f"💰 {cheapest['price']} USD\n"
                    f"📊 %{diff_percent:.1f} fark\n\n"
                    f"https://sorare.com/nba/cards/{cheapest['slug']}"
                )
                seen["price"][key] = True

    save_seen(seen)

# ================== ÇALIŞTIR ==================

if __name__ == "__main__":
    run()