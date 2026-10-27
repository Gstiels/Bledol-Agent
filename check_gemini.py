import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

key = os.getenv("GEMINI_API_KEY")
models = ["gemini-flash-lite-latest", "gemini-flash-latest"]

prompt = (
    "Write one short Instagram caption (max 40 words) for Bledol Integrated "
    "Services, an Abuja company offering BIM construction drawings and "
    "epoxy flooring. Professional tone, end with 3 hashtags."
)

for model in models:
    for attempt in range(1, 4):
        try:
            response = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                headers={"x-goog-api-key": key},
                json={"contents": [{"parts": [{"text": prompt}]}]},
                timeout=90,
            )
        except requests.exceptions.RequestException as e:
            print(f"{model}, attempt {attempt}: {type(e).__name__}")
            time.sleep(5 * attempt)
            continue

        if response.status_code == 200:
            data = response.json()
            print(f"({model})")
            print(data["candidates"][0]["content"]["parts"][0]["text"])
            raise SystemExit

        print(f"{model}, attempt {attempt}: {response.status_code}")
        if response.status_code in (429, 500, 503):
            time.sleep(5 * attempt)
        else:
            print(response.json())
            raise SystemExit

print("All attempts failed. Try again in a few minutes.")