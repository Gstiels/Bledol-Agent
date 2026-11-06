import glob
import json
import os
import time

import requests
from dotenv import load_dotenv

load_dotenv()

GRAPH = "https://graph.facebook.com/v26.0"
PAGE_ID = os.getenv("PAGE_ID")
IG_ID = os.getenv("IG_USER_ID")
TOKEN = os.getenv("PAGE_TOKEN")


def graph_post(path, data):
    data = dict(data, access_token=TOKEN)
    response = requests.post(f"{GRAPH}/{path}", data=data, timeout=90)
    body = response.json()
    if "error" in body:
        raise RuntimeError(body["error"].get("message", body["error"]))
    return body


def post_to_facebook(draft):
    body = graph_post(
        f"{PAGE_ID}/photos",
        {"url": draft["image_url"], "caption": draft["facebook"]},
    )
    return body.get("post_id") or body.get("id")


def post_to_instagram(draft):
    container = graph_post(
        f"{IG_ID}/media",
        {"image_url": draft["image_url"], "caption": draft["instagram"]},
    )["id"]
    for _ in range(10):
        status = requests.get(
            f"{GRAPH}/{container}",
            params={"fields": "status_code", "access_token": TOKEN},
            timeout=30,
        ).json()
        if status.get("status_code") == "FINISHED":
            break
        if status.get("status_code") == "ERROR":
            raise RuntimeError("Instagram could not process the photo")
        time.sleep(3)
    return graph_post(f"{IG_ID}/media_publish", {"creation_id": container})["id"]


def load_pending():
    pending = []
    for path in sorted(glob.glob(os.path.join("drafts", "*.json"))):
        if os.path.basename(path) == "used.json":
            continue
        with open(path, encoding="utf-8") as f:
            draft = json.load(f)
        if draft.get("status") == "pending":
            pending.append((path, draft))
    return pending


def save(path, draft):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(draft, f, indent=2, ensure_ascii=False)


def main():
    pending = load_pending()
    if not pending:
        print("No pending drafts. Run python auto_draft.py first.")
        return

    for path, draft in pending:
        print("=" * 60)
        print(f"Draft {draft['id']}  ({draft.get('photo_name', '')})")
        print(f"Photo: {draft['image_url']}\n")
        print("INSTAGRAM:\n" + draft["instagram"] + "\n")
        print("FACEBOOK:\n" + draft["facebook"] + "\n")

        choice = input("Type YES to publish to both, NO to reject, or press Enter to skip: ").strip().upper()

        if choice == "NO":
            draft["status"] = "rejected"
            save(path, draft)
            print("Rejected.\n")
        elif choice == "YES":
            if not draft.get("facebook_post_id"):
                try:
                    draft["facebook_post_id"] = post_to_facebook(draft)
                    print("Facebook: posted")
                except Exception as e:
                    print(f"Facebook failed: {e}")
            if not draft.get("instagram_media_id"):
                try:
                    draft["instagram_media_id"] = post_to_instagram(draft)
                    print("Instagram: posted")
                except Exception as e:
                    print(f"Instagram failed: {e}")
            if draft.get("facebook_post_id") and draft.get("instagram_media_id"):
                draft["status"] = "published"
            save(path, draft)
            print()
        else:
            print("Skipped.\n")


if __name__ == "__main__":
    main()