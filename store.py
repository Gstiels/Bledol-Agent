import json
import os

STATE_FILE = os.path.join("state", "state.json")


def load():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    state = {"seen": [], "fingerprints": [], "drafts": {}}
    # Photos the earlier version already handled, so nothing is posted twice
    old_used = os.path.join("drafts", "used.json")
    if os.path.exists(old_used):
        with open(old_used, encoding="utf-8") as f:
            state["seen"] = json.load(f)
    return state


def save(state):
    os.makedirs("state", exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)