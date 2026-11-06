import os
import time

import requests
from dotenv import load_dotenv

load_dotenv()

GRAPH = "https://graph.facebook.com/v26.0"


def _post(path, data):
    data = dict(data, access_token=os.getenv("PAGE_TOKEN"))
    response = requests.post(f"{GRAPH}/{path}", data=data, timeout=90)
    body = response.json()
    if "error" in body:
        raise RuntimeError(body["error"].get("message", body["error"]))
    return body


def post_to_facebook(image_url, caption):
    body = _post(
        f"{os.getenv('PAGE_ID')}/photos",
        {"url": image_url, "caption": caption},
    )
    return body.get("post_id") or body.get("id")


def post_to_instagram(image_url, caption):
    ig = os.getenv("IG_USER_ID")
    container = _post(f"{ig}/media", {"image_url": image_url, "caption": caption})["id"]
    for _ in range(10):
        status = requests.get(
            f"{GRAPH}/{container}",
            params={"fields": "status_code", "access_token": os.getenv("PAGE_TOKEN")},
            timeout=30,
        ).json()
        if status.get("status_code") == "FINISHED":
            break
        if status.get("status_code") == "ERROR":
            raise RuntimeError("Instagram could not process the photo")
        time.sleep(3)
    return _post(f"{ig}/media_publish", {"creation_id": container})["id"]