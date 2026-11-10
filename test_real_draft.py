import os
import requests
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("TELEGRAM_BOT_TOKEN")
chat_id = os.getenv("TELEGRAM_CHAT_ID")

url = f"https://api.telegram.org/bot{token}/sendMessage"

# Simulating draft ID 101
draft_id = "101"
text = f"📸 *New Draft Ready!*\n\nProject: Test Post\nPhoto: test_image.jpg\n\nDraft ID: {draft_id}"

payload = {
    "chat_id": chat_id,
    "text": text,
    "parse_mode": "Markdown",
    "reply_markup": {
        "inline_keyboard": [
            [
                {"text": "✅ Approve", "callback_data": f"approve_{draft_id}"},
                {"text": "✏️ Edit", "callback_data": f"edit_{draft_id}"},
                {"text": "❌ Reject", "callback_data": f"reject_{draft_id}"}
            ]
        ]
    }
}

response = requests.post(url, json=payload)
print("Sent realistic draft! Check your phone.")