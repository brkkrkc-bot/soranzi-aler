import os
import json
import time
import requests

# ================== AYARLAR ==================

SORARE_API = "https://api.sorare.com/graphql"

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

SEEN_FILE = "seen.json"

CHECK_INTERVAL = 300  # 5 dakika

# Takip edeceğin oyuncular (slug: isim)
PLAYERS = {
    "jaren-jackson-jr": "Jaren Jackson Jr",
    "tyler-herro": "Tyler Herro",
    "tyrese-maxey": "Tyrese Maxey",
    "giannis-antetokounmpo": "Giannis Antetokounmpo"
}

# ================== TELEGRAM ==================

def send_telegram(msg: str):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": msg})

# ================== SEEN ==================

def load_seen():
    if not os.path.exists(SEEN_FILE):
        return {}
    with open(SEEN_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_seen(data):
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

# ================== SORARE ==================

def fetch_cards(player_slug):
    query = """
    query PlayerCards($slug: String!) {
      players(slugs: [$slug]) {
        slug
        displayName
        cards(first: 20, rarities: [limited], orderBy: CREATED_AT_DESC) {
          nodes {
            id
            name
            rarity
            createdAt
          }
        }
      }
    }
    """

    r = requests.post(
        SORARE_API,
        json={
            "query": query,
            "variables": {"slug": player_slug}
        },
        headers={"Content-Type": "application/json"},
        timeout=30
    )

    r.raise_for_status()
    j = r.json()

    if "errors" in j:
        raise Exception(j["errors"])

    players = j["data"]["players"]
    if not players:
        return []

    return players[0]["cards"]["nodes"]

# ================== MAIN ==================

def run():
    seen = load_seen()

    send_telegram("🟢 Sorare NBA LIMITED price checker başladı")

    while True:
        for slug, name in PLAYERS.items():
            try:
                cards = fetch_cards(slug)

                for card in cards:
                    cid = card["id"]

                    if cid in seen:
                        continue

                    seen[cid] = {
                        "player": name,
                        "createdAt": card["createdAt"]
                    }

                    msg = (
                        f"🆕 YENİ KART!\n"
                        f"🏀 {name}\n"
                        f"🎴 {card['rarity'].upper()}\n"
                        f"🕒 {card['createdAt']}"
                    )
                    send_telegram(msg)

                save_seen(seen)

            except Exception as e:
                send_telegram(f"⚠️ Hata ({name}): {e}")

        time.sleep(CHECK_INTERVAL)

# ================== ENTRY ==================

if __name__ == "__main__":
    run()
