import os
import json
import time
import requests
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise SystemExit("TELEGRAM_BOT_TOKEN is missing in .env")

BASE_URL = f"https://api.telegram.org/bot{TOKEN}"
STATE_FILE = "state/state.json"

def get_updates(offset=None):
    url = f"{BASE_URL}/getUpdates"
    params = {"timeout": 30}
    if offset:
        params["offset"] = offset
    try:
        r = requests.get(url, params=params, timeout=35)
        return r.json()
    except requests.exceptions.RequestException as e:
        print(f"Network error: {e}")
        return None

def answer_callback(callback_id, text):
    requests.post(f"{BASE_URL}/answerCallbackQuery", json={
        "callback_query_id": callback_id,
        "text": text
    })

def edit_message(chat_id, message_id, text):
    requests.post(f"{BASE_URL}/editMessageText", json={
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text
    })

def update_state(draft_id, status):
    if not os.path.exists(STATE_FILE):
        print(f"Warning: {STATE_FILE} not found.")
        return
    
    with open(STATE_FILE, "r") as f:
        state = json.load(f)
    
    # Assuming state.json has a "drafts" list
    if "drafts" in state:
        for draft in state["drafts"]:
            # If your drafts have IDs, match them. Otherwise, update the first pending one.
            if str(draft.get("id")) == str(draft_id) or draft.get("status") == "pending":
                draft["status"] = status
                print(f"Updated draft {draft_id} to {status}")
                break
        
        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)

def main():
    print("Listening for Telegram button clicks... (Press Ctrl+C to stop)")
    # Delete any webhooks so polling works
    requests.get(f"{BASE_URL}/deleteWebhook")
    
    offset = None
    while True:
        data = get_updates(offset)
        if not data or not data.get("ok"):
            time.sleep(2)
            continue

        for update in data["result"]:
            offset = update["update_id"] + 1
            
            # Check if it's a button click
            if "callback_query" in update:
                cb = update["callback_query"]
                cb_id = cb["id"]
                msg = cb["message"]
                chat_id = msg["chat"]["id"]
                message_id = msg["message_id"]
                
                # Data comes from the button clicked (e.g., "approve_123")
                data_str = cb.get("data", "")
                parts = data_str.split("_")
                action = parts[0]
                draft_id = parts[1] if len(parts) > 1 else "unknown"

                if action == "approve":
                    answer_callback(cb_id, "Approved! ✅")
                    edit_message(chat_id, message_id, f"{msg['text']}\n\n✅ APPROVED")
                    update_state(draft_id, "approved")
                elif action == "reject":
                    answer_callback(cb_id, "Rejected ❌")
                    edit_message(chat_id, message_id, f"{msg['text']}\n\n❌ REJECTED")
                    update_state(draft_id, "rejected")
                elif action == "edit":
                    answer_callback(cb_id, "Edit mode...")
                    # For now, just acknowledge it. We'll build the edit flow later.
                    edit_message(chat_id, message_id, f"{msg['text']}\n\n✏️ EDIT REQUESTED")

if __name__ == "__main__":
    main()