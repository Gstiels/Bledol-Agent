import json
import os
import re
import sys
from datetime import datetime

import requests
from dotenv import load_dotenv

from captions import write_posts

load_dotenv()

DRAFTS = "drafts"
USED_FILE = os.path.join(DRAFTS, "used.json")


def list_cloudinary_photos():
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
    photos.sort(key=lambda p: p["created_at"], reverse=True)  # newest first
    return photos


def name_to_note(photo):
    name = photo.get("display_name") or photo["public_id"].split("/")[-1]
    words = re.sub(r"[-_]+", " ", name).strip()
    real_words = [w for w in words.split() if w.isalpha() and len(w) >= 3]
    if len(real_words) < 2:
        return None, name
    note = (
        f"Project photo named: {words}. "
        "This name is the only information known about the project."
    )
    return note, name


def as_jpg(url):
    """Instagram needs JPG, so ask Cloudinary to deliver the photo as .jpg"""
    base, slash, last = url.rpartition("/")
    name = last.split("?")[0]
    if "." in name:
        name = name.rsplit(".", 1)[0]
    return f"{base}{slash}{name}.jpg"


def load_used():
    if os.path.exists(USED_FILE):
        with open(USED_FILE, encoding="utf-8") as f:
            return json.load(f)
    return []


def save_used(used):
    with open(USED_FILE, "w", encoding="utf-8") as f:
        json.dump(used, f, indent=2)


def main():
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    os.makedirs(DRAFTS, exist_ok=True)
    used = load_used()
    made = 0

    for photo in list_cloudinary_photos():
        if made >= count:
            break
        public_id = photo["public_id"]
        if public_id in used:
            continue

        note, name = name_to_note(photo)
        if note is None:
            print(f"Skipped '{name}': rename it to describe the project, e.g. epoxy-floor-idu-warehouse")
            continue

        image_url = as_jpg(photo["secure_url"])
        check = requests.head(image_url, timeout=30, allow_redirects=True)
        if check.status_code != 200:
            print(f"Skipped '{name}': photo link did not open (status {check.status_code})")
            continue

        print(f"Writing drafts for '{name}'...")
        posts = write_posts(note)

        draft_id = datetime.now().strftime("%Y%m%d-%H%M%S") + f"-{made + 1}"
        draft = {
            "id": draft_id,
            "status": "pending",
            "photo_name": name,
            "note": note,
            "image_url": image_url,
            "instagram": posts["instagram"],
            "facebook": posts["facebook"],
        }
        path = os.path.join(DRAFTS, f"{draft_id}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(draft, f, indent=2, ensure_ascii=False)

        used.append(public_id)
        save_used(used)
        made += 1

        print(f"Draft saved: {path}")
        print(f"Photo: {image_url}")
        print("\n--- INSTAGRAM ---")
        print(posts["instagram"])
        print("\n--- FACEBOOK ---")
        print(posts["facebook"])
        print()

    if made == 0:
        print("No new photos with descriptive names found.")


if __name__ == "__main__":
    main()