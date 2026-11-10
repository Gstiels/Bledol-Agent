import os

import requests
from dotenv import load_dotenv

import store

load_dotenv()

token = os.getenv("TELEGRAM_BOT_TOKEN")
chat = os.getenv("TELEGRAM_CHAT_ID")
if not token or not chat:
    raise SystemExit("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is missing in .env")

API = f"https://api.telegram.org/bot{token}"


def send(method, **data):
    r = requests.post(f"{API}/{method}", data={"chat_id": chat, **data}, timeout=60)
    result = r.json()
    if result.get("ok"):
        print(f"OK: {method}")
    else:
        print(f"FAILED: {method} -> {result.get('description')}")


state = store.load()
drafts = list(state["drafts"].values())
if not drafts:
    raise SystemExit("No drafts in state/state.json to send.")
draft = drafts[-1]

send("sendPhoto", photo=draft["image_url"], caption=draft["photo_name"])
send("sendMessage", text="INSTAGRAM:\n" + draft["instagram"])
send("sendMessage", text="FACEBOOK:\n" + draft["facebook"])