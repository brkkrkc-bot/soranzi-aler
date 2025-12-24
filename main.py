import os
import json
import time
import requests

# ================== AYARLAR ==================

SORARE_API = "https://api.sorare.com/graphql"

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

SEEN_FILE = "seen.json"
STATUS_FILE = "status.json"
PLAYERS_FILE = "players.json"

CHECK_INTERVAL = 60  # saniye
RARITY = "limited"

# ================== YARDIMCI ==================

def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def send_telegram(msg):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

# ================== SORARE NBA ==================

def fetch_cards(slug):
    query = """
    query NbaPlayerCards($slug: String!) {
      nbaPlayer(slug: $slug) {
        displayName
        cards(first: 20, rarities: [limited], orderBy: CREATED_AT_DESC) {
          nodes {
            id
            name
            createdAt
          }
        }
      }
    }
    """

    r = requests.post(
        SORARE_API,
        json={"query": query, "variables": {"slug": slug}},
        headers={"Content-Type": "application/json"},
        timeout=30
    )

    r.raise_for_status()
    j = r.json()

    if "errors" in j:
        raise Exception(j["errors"])

    player = j["data"]["nbaPlayer"]
    if not player:
        return None, []

    return player["displayName"], player["cards"]["nodes"]

# ================== MAIN ==================

def main():
    players = load_json(PLAYERS_FILE, {})
    seen = load_json(SEEN_FILE, {})
    status = load_json(STATUS_FILE, {"started": False})

    # 🔔 Sadece ilk çalışmada bildirim
    if not status.get("started"):
        send_telegram("🟢 Sorare NBA LIMITED price checker başladı")
        status["started"] = True
        save_json(STATUS_FILE, status)

    for slug, label in players.items():
        try:
            name, cards = fetch_cards(slug)
            if not cards:
                continue

            last_seen_id = seen.get(slug)
            newest = cards[0]["id"]

            # 🆕 Yeni kart varsa
            if last_seen_id and newest != last_seen_id:
                send_telegram(
                    f"🆕 Yeni {RARITY.upper()} kart!\n"
                    f"👤 {name}\n"
                    f"🆔 {newest}"
                )

            seen[slug] = newest

        except Exception as e:
            # ⚠️ API hatası – spam yapmasın diye sadece print
            print(f"Hata ({slug}):", e)

    save_json(SEEN_FILE, seen)

# ================== LOOP ==================

if __name__ == "__main__":
    main()