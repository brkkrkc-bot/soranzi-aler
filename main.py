import os
import requests
import time

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

PLAYERS = [
    "tyrese-maxey",
    "shai-gilgeous-alexander",
    "giannis-antetokounmpo",
    "pascal-siakam",
    "cade-cunningham"
]

def send_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text})

send_message("✅ Sorare NBA checker çalıştı. (test mesajı)")
