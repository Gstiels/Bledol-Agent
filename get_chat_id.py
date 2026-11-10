import os

import requests
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("TELEGRAM_BOT_TOKEN")
if not token:
    raise SystemExit("TELEGRAM_BOT_TOKEN is missing in .env")

r = requests.get(f"https://api.telegram.org/bot{token}/getUpdates", timeout=30)
data = r.json()
if not data.get("ok"):
    raise SystemExit(f"Telegram error: {data}")

seen = {}
for update in data["result"]:
    message = update.get("message")
    if message:
        chat = message["chat"]
        seen[chat["id"]] = chat.get("first_name") or chat.get("title") or "?"

if not seen:
    print("No messages found. Send 'hello' to your bot in Telegram, then run this again.")
for chat_id, name in seen.items():
    print(f"Chat ID: {chat_id}   (chat with {name})")