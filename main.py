iimport os
import requests

def send_message(text):
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("CHAT_ID")

    if not token or not chat_id:
        print("ENV VAR YOK")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text
    }

    r = requests.post(url, data=payload)
    print("Telegram response:", r.text)

print("MAIN.PY ÇALIŞTI")

send_message("🟢 TEST OK: main.py çalıştı ve Telegram'a ulaştı")