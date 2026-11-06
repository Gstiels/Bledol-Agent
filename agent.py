import os
import re
import sys
from datetime import datetime

import requests
from dotenv import load_dotenv

import publisher
import store
from captions import write_posts

load_dotenv()


def list_photos():
    cloud = os.getenv("CLOUDINARY_CLOUD_NAME")
    response = requests.get(
        f"https://api.cloudinary.com/v1_1/{cloud}/resources/image",
        params={"type": "upload", "max_results": 100},
        auth=(os.getenv("CLOUDINARY_API_KEY"), os.getenv("CLOUDINARY_API_SECRET")),
        timeout=60,
    )
    data = response.json()
    if response.status_code != 200:
        raise RuntimeError(f"Cloudinary error: {data}")
    photos = data["resources"]
    photos.sort(key=lambda p: p["created_at"])  # oldest first
    return photos


def fingerprint(photo):
    return f"{photo.get('bytes')}-{photo.get('width')}x{photo.get('height')}"


def photo_name(photo):
    return photo.get("display_name") or photo["public_id"].split("/")[-1]


def name_to_note(name):
    words = re.sub(r"[-_]+", " ", name).strip()
    real = [w for w in words.split() if w.isalpha() and len(w) >= 3]
    if len(real) < 2:
        return None
    return (
        f"Project photo named: {words}. "
        "This name is the only information known about the project."
    )


def as_jpg(url):
    """Instagram needs JPG, so ask Cloudinary to deliver the photo as .jpg"""
    base, slash, last = url.rpartition("/")
    name = last.split("?")[0]
    if "." in name:
        name = name.rsplit(".", 1)[0]
    return f"{base}{slash}{name}.jpg"


def make_new_drafts(state, limit=1):
    made = 0
    for photo in list_photos():
        public_id = photo["public_id"]
        fp = fingerprint(photo)
        name = photo_name(photo)

        # Ignore the sample images that come with every Cloudinary account
        if public_id == "sample" or public_id.startswith(("samples/", "cld-sample")):
            continue

        if public_id in state["seen"]:
            if fp not in state["fingerprints"]:
                state["fingerprints"].append(fp)
            continue
        if made >= limit:
            break
        if fp in state["fingerprints"]:
            print(f"Skipped '{name}': same photo as one already handled")
            state["seen"].append(public_id)
            store.save(state)
            continue

        note = name_to_note(name)
        if note is None:
            print(f"Skipped '{name}': rename it to describe the project, e.g. epoxy-floor-idu-warehouse")
            continue

        image_url = as_jpg(photo["secure_url"])
        if requests.head(image_url, timeout=30, allow_redirects=True).status_code != 200:
            print(f"Skipped '{name}': photo link did not open")
            continue

        print(f"Writing drafts for '{name}'...")
        posts = write_posts(note)
        draft_id = datetime.now().strftime("%Y%m%d-%H%M%S") + f"-{made + 1}"
        state["drafts"][draft_id] = {
            "status": "pending",
            "photo_name": name,
            "image_url": image_url,
            "instagram": posts["instagram"],
            "facebook": posts["facebook"],
        }
        state["seen"].append(public_id)
        state["fingerprints"].append(fp)
        store.save(state)
        made += 1
    return made


def publish(state, draft):
    if not draft.get("facebook_post_id"):
        try:
            draft["facebook_post_id"] = publisher.post_to_facebook(
                draft["image_url"], draft["facebook"]
            )
            print("Facebook: posted")
        except Exception as e:
            print(f"Facebook failed: {e}")
        store.save(state)
    if not draft.get("instagram_media_id"):
        try:
            draft["instagram_media_id"] = publisher.post_to_instagram(
                draft["image_url"], draft["instagram"]
            )
            print("Instagram: posted")
        except Exception as e:
            print(f"Instagram failed: {e}")
        store.save(state)
    if draft.get("facebook_post_id") and draft.get("instagram_media_id"):
        draft["status"] = "published"
        store.save(state)


def review_in_console(state):
    pending = [(i, d) for i, d in state["drafts"].items() if d["status"] == "pending"]
    if not pending:
        print("No pending drafts.")
        return
    for draft_id, draft in pending:
        print("=" * 60)
        print(f"Draft {draft_id}  ({draft['photo_name']})")
        print(f"Photo: {draft['image_url']}\n")
        print("INSTAGRAM:\n" + draft["instagram"] + "\n")
        print("FACEBOOK:\n" + draft["facebook"] + "\n")
        choice = input("Type YES to publish to both, NO to reject, or press Enter to skip: ").strip().upper()
        if choice == "NO":
            draft["status"] = "rejected"
            store.save(state)
            print("Rejected.\n")
        elif choice == "YES":
            publish(state, draft)
            print()
        else:
            print("Skipped.\n")


def main():
    state = store.load()
    made = make_new_drafts(state)
    store.save(state)
    print(f"{made} new draft(s) created.")
    if "--console" in sys.argv:
        review_in_console(state)


if __name__ == "__main__":
    main()