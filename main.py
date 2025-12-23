import os
import requests

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("CHAT_ID")


def send_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": int(TELEGRAM_CHAT_ID),
        "text": text
    }
    r = requests.post(url, json=payload, timeout=10)
    print(r.status_code, r.text)


def run():
    send_message("TEST OK")
    return


if __name__ == "__main__":
    run()