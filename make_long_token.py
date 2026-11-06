import getpass
import os
from datetime import datetime

import requests
from dotenv import load_dotenv, set_key

load_dotenv()

GRAPH = "https://graph.facebook.com/v26.0"
APP_ID = os.getenv("APP_ID")
APP_SECRET = os.getenv("APP_SECRET")
PAGE_ID = os.getenv("PAGE_ID")
BUSINESS_ID = "470426368302517"


def get(path, **params):
    response = requests.get(f"{GRAPH}/{path}", params=params, timeout=30)
    return response.json()


def main():
    if not APP_ID or not APP_SECRET:
        raise SystemExit("Add APP_ID and APP_SECRET to .env first.")

    short = getpass.getpass(
        "Paste the short-lived USER token (nothing will show as you paste), then press Enter: "
    ).strip()

    # 1. Short-lived user token -> long-lived user token (about 60 days)
    body = get(
        "oauth/access_token",
        grant_type="fb_exchange_token",
        client_id=APP_ID,
        client_secret=APP_SECRET,
        fb_exchange_token=short,
    )
    if "error" in body:
        raise SystemExit(f"Facebook error: {body['error'].get('message')}")
    long_user = body["access_token"]
    print("Got a long-lived user token.")

    # 2. Use it to get the Bledol Page token
    page_token = None
    for edge in (f"{BUSINESS_ID}/owned_pages", "me/accounts"):
        pages = get(edge, fields="id,name,access_token", access_token=long_user)
        for page in pages.get("data", []):
            if page["id"] == PAGE_ID and "access_token" in page:
                page_token = page["access_token"]
                break
        if page_token:
            break
    if not page_token:
        raise SystemExit(
            "Could not find the Bledol Page token. Check that the short-lived "
            "token was made with the Bledol Page selected and the permissions ticked."
        )

    # 3. Check what the Page token is allowed to do and when it expires
    info = get(
        "debug_token",
        input_token=page_token,
        access_token=f"{APP_ID}|{APP_SECRET}",
    ).get("data", {})
    expires = info.get("expires_at", 0)
    print("Token valid:", info.get("is_valid"))
    print("Expires:", "never" if expires == 0 else datetime.fromtimestamp(expires))
    print("Permissions:", ", ".join(info.get("scopes", [])))

    # 4. Save it into .env as PAGE_TOKEN
    set_key(".env", "PAGE_TOKEN", page_token, quote_mode="never")
    print("\nSaved the new Page token to .env as PAGE_TOKEN.")


if __name__ == "__main__":
    main()