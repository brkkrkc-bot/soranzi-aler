import os
import json
import time
import requests

# ================== AYARLAR ==================

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

SORARE_API = "https://api.sorare.com/graphql"
SEEN_FILE = "seen.json"

PERCENT_ALERT = 15
CHECK_INTERVAL = 300  # 5 dk

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
    requests.post(url, data={"chat_id": CHAT_ID, "text": text}, timeout=10)

def safe_price(v):
    try:
        return float(v)
    except:
        return None

# ================== SORARE ==================

def fetch_cards(slug):
    query = """
    query PlayerCards($slug: String!) {
      player(slug: $slug) {
        cards(first: 20, rarities: [limited], onSale: true) {
          nodes {
            slug
            price
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
    if not data.get("data") or not data["data"]["player"]:
        return []
    return data["data"]["player"]["cards"]["nodes"]

def fetch_last_sales(slug):
    query = """
    query LastSales($slug: String!) {
      player(slug: $slug) {
        cards(first: 5, rarities: [limited]) {
          nodes {
            latestSalePrice
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
    if not data.get("data") or not data["data"]["player"]:
        return []

    prices = []
    for c in data["data"]["player"]["cards"]["nodes"]:
        p = safe_price(c.get("latestSalePrice"))
        if p:
            prices.append(p)
    return prices

# ================== ANA LOOP ==================

def run():
    send_message("🟢 Sorare NBA LIMITED price checker başladı")
    seen = load_seen()

    while True:
        try:
            for slug, name in PLAYERS.items():
                cards = fetch_cards(slug)
                cards = [c for c in cards if safe_price(c["price"])]

                if len(cards) < 2:
                    continue

                cards = sorted(cards, key=lambda x: safe_price(x["price"]))
                cheapest = cards[0]
                second = cards[1]

                p1 = safe_price(cheapest["price"])
                p2 = safe_price(second["price"])

                # ===== SON 5 SATIŞ ORT =====
                last_sales = fetch_last_sales(slug)
                avg_last5 = sum(last_sales) / len(last_sales) if last_sales else None

                # ===== 1️⃣ YENİ IN-SEASON =====
                if cheapest["isInSeason"]:
                    cid = cheapest["slug"]
                    if cid not in seen["new_card"]:
                        send_message(
                            f"🆕 YENİ IN-SEASON\n\n"
                            f"👤 {name}\n"
                            f"💰 {p1} USD\n\n"
                            f"https://sorare.com/nba/cards/{cid}"
                        )
                        seen["new_card"][cid] = True

                # ===== 2️⃣ FLOOR ALTI =====
                diff_floor = ((p2 - p1) / p2) * 100
                if diff_floor > 0:
                    key = cheapest["slug"]
                    if key not in seen["price"]:
                        send_message(
                            f"🔥 FLOOR ALTI\n\n"
                            f"👤 {name}\n"
                            f"💰 {p1} USD\n"
                            f"📉 Floor: {p2} USD\n"
                            f"📊 %{diff_floor:.1f}\n\n"
                            f"https://sorare.com/nba/cards/{key}"
                        )
                        seen["price"][key] = True

                # ===== 3️⃣ % FARK (SON 5 SATIŞ) =====
                if avg_last5:
                    diff_last5 = ((avg_last5 - p1) / avg_last5) * 100
                    key = cheapest["slug"] + "_last5"
                    if diff_last5 >= PERCENT_ALERT and key not in seen["price"]:
                        send_message(
                            f"⚡ % FARK (SON 5 SATIŞ)\n\n"
                            f"👤 {name}\n"
                            f"💰 Şu an: {p1} USD\n"
                            f"📈 Son 5 ort: {avg_last5:.2f} USD\n"
                            f"📊 %{diff_last5:.1f}\n\n"
                            f"https://sorare.com/nba/cards/{cheapest['slug']}"
                        )
                        seen["price"][key] = True

            save_seen(seen)
            time.sleep(CHECK_INTERVAL)

        except Exception as e:
            send_message(f"❌ BOT HATASI:\n{e}")
            time.sleep(60)

# ================== START ==================

if __name__ == "__main__":
    run()