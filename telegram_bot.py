import os
import time

import requests

import store
from captions import BRAND_GUIDE, ask_gemini


def configured():
    return bool(os.getenv("TELEGRAM_BOT_TOKEN") and os.getenv("TELEGRAM_CHAT_ID"))


def _call(method, **params):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    response = requests.post(
        f"https://api.telegram.org/bot{token}/{method}", json=params, timeout=60
    )
    data = response.json()
    if not data.get("ok"):
        raise RuntimeError(f"Telegram {method} failed: {data.get('description')}")
    return data["result"]


def _chat():
    return str(os.getenv("TELEGRAM_CHAT_ID"))


def _say(text):
    _call("sendMessage", chat_id=_chat(), text=text)


def _send_buttons(draft_id, draft, heading):
    text = (
        f"{heading} {draft_id}\n\n"
        f"INSTAGRAM:\n{draft['instagram']}\n\n"
        f"FACEBOOK:\n{draft['facebook']}"
    )
    keyboard = [[
        {"text": "Approve", "callback_data": f"approve:{draft_id}"},
        {"text": "Edit", "callback_data": f"edit:{draft_id}"},
        {"text": "Reject", "callback_data": f"reject:{draft_id}"},
    ]]
    _call(
        "sendMessage",
        chat_id=_chat(),
        text=text[:4000],
        reply_markup={"inline_keyboard": keyboard},
    )


def send_pending(state):
    """Send every pending draft that has not been sent to Telegram yet."""
    for draft_id, draft in state["drafts"].items():
        if draft["status"] == "pending" and not draft.get("sent"):
            try:
                _call(
                    "sendPhoto",
                    chat_id=_chat(),
                    photo=draft["image_url"],
                    caption=draft["photo_name"],
                )
                _send_buttons(draft_id, draft, "Draft")
                draft["sent"] = True
                store.save(state)
                print(f"Sent draft {draft_id} to Telegram")
            except Exception as e:
                print(f"Could not send draft {draft_id}: {e}")


def _parse(text):
    try:
        after = text.split("INSTAGRAM:", 1)[1]
        instagram, facebook = after.split("FACEBOOK:", 1)
        return instagram.strip(), facebook.strip()
    except (IndexError, ValueError):
        return None


def _rewrite(draft, instruction):
    prompt = (
        f"{BRAND_GUIDE}\n\n"
        "Here are the current drafts.\n\n"
        f"INSTAGRAM:\n{draft['instagram']}\n\n"
        f"FACEBOOK:\n{draft['facebook']}\n\n"
        f"Change them as follows: {instruction}\n"
        "Do not add claims that are not already in the drafts or in the instruction. "
        "Reply in exactly this format:\nINSTAGRAM:\n<text>\nFACEBOOK:\n<text>"
    )
    return _parse(ask_gemini(prompt))


def _result_text(draft):
    if os.getenv("DRY_RUN"):
        return "Dry run: nothing was posted."
    fb = bool(draft.get("facebook_post_id"))
    ig = bool(draft.get("instagram_media_id"))
    text = f"Facebook: {'posted' if fb else 'FAILED'}\nInstagram: {'posted' if ig else 'FAILED'}"
    if not (fb and ig):
        text += "\nTap Approve again on the draft to retry the failed one."
    return text


def _handle(state, update, publish):
    callback = update.get("callback_query")
    if callback:
        if str(callback["message"]["chat"]["id"]) != _chat():
            return
        try:
            _call("answerCallbackQuery", callback_query_id=callback["id"])
        except Exception:
            pass
        action, _, draft_id = callback.get("data", "").partition(":")
        if action not in ("approve", "edit", "reject"):
            return
        draft = state["drafts"].get(draft_id)
        if not draft:
            print(f"Tap for unknown draft {draft_id}")
            return
        if draft["status"] != "pending":
            _say(f"Draft {draft_id} is already {draft['status']}.")
            return
        if action == "approve":
            _say("Posting to Facebook and Instagram...")
            publish(state, draft)
            _say(_result_text(draft))
        elif action == "reject":
            draft["status"] = "rejected"
            if state.get("editing") == draft_id:
                state.pop("editing")
            _say(f"Draft {draft_id} rejected.")
        elif action == "edit":
            state["editing"] = draft_id
            _say(
                "Send your change, for example: make it shorter, or mention Abuja.\n"
                "Or paste the full new text, with INSTAGRAM: first and FACEBOOK: second.\n"
                "Send /cancel to stop editing."
            )
        return

    message = update.get("message")
    if not message or str(message["chat"]["id"]) != _chat() or not message.get("text"):
        return
    draft_id = state.get("editing")
    if not draft_id:
        return
    text = message["text"].strip()
    if text == "/cancel":
        state.pop("editing")
        _say("Editing cancelled.")
        return
    draft = state["drafts"].get(draft_id)
    if not draft or draft["status"] != "pending":
        state.pop("editing")
        return
    if "INSTAGRAM:" in text and "FACEBOOK:" in text:
        new_posts = _parse(text)
    else:
        new_posts = _rewrite(draft, text)
    if not new_posts:
        _say("I could not use that. Try again, or send /cancel.")
        return
    draft["instagram"], draft["facebook"] = new_posts
    state.pop("editing")
    _send_buttons(draft_id, draft, "Updated draft")


def _awaiting(state):
    if state.get("editing"):
        return True
    return any(d["status"] == "pending" and d.get("sent") for d in state["drafts"].values())


def process_updates(state, publish, wait_seconds=0):
    """Act on button taps and replies. With wait_seconds, keep listening that long."""
    deadline = time.time() + wait_seconds
    while True:
        params = {
            "timeout": 25 if wait_seconds else 0,
            "allowed_updates": ["message", "callback_query"],
        }
        if "tg_offset" in state:
            params["offset"] = state["tg_offset"]
        try:
            updates = _call("getUpdates", **params)
        except Exception as e:
            print(f"Telegram check failed: {e}")
            return
        for update in updates:
            state["tg_offset"] = update["update_id"] + 1
            try:
                _handle(state, update, publish)
            except Exception as e:
                print(f"Telegram update error: {e}")
            store.save(state)
        if time.time() >= deadline or not _awaiting(state):
            break