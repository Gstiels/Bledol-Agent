import json
import os
import sys
from datetime import datetime

import requests

from captions import write_posts


def as_jpg(url):
    """Instagram needs JPG, so ask Cloudinary to deliver the photo as .jpg"""
    base, slash, last = url.rpartition("/")
    name = last.split("?")[0]
    if "." in name:
        name = name.rsplit(".", 1)[0]
    return f"{base}{slash}{name}.jpg"


def main():
    if len(sys.argv) < 3:
        print('Usage: python make_draft.py "cloudinary-photo-url" "project note"')
        sys.exit(1)

    image_url, note = sys.argv[1], sys.argv[2]
    if not image_url.startswith("https://res.cloudinary.com/"):
        sys.exit("The photo link must be a Cloudinary link starting with https://res.cloudinary.com/")

    image_url = as_jpg(image_url)
    check = requests.head(image_url, timeout=30, allow_redirects=True)
    if check.status_code != 200:
        sys.exit(f"Could not open the photo link (status {check.status_code}). Check the link.")

    print("Writing captions...")
    posts = write_posts(note)

    os.makedirs("drafts", exist_ok=True)
    draft_id = datetime.now().strftime("%Y%m%d-%H%M%S")
    draft = {
        "id": draft_id,
        "status": "pending",
        "note": note,
        "image_url": image_url,
        "instagram": posts["instagram"],
        "facebook": posts["facebook"],
    }
    path = f"drafts/{draft_id}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(draft, f, indent=2, ensure_ascii=False)

    print(f"\nDraft saved: {path}")
    print(f"Photo: {image_url}")
    print("\n--- INSTAGRAM ---")
    print(posts["instagram"])
    print("\n--- FACEBOOK ---")
    print(posts["facebook"])


if __name__ == "__main__":
    main()