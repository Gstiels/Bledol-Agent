import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

MODELS = ["gemini-flash-lite-latest", "gemini-flash-latest"]

BRAND_GUIDE = """
You write social media posts for Bledol Integrated Services LTD, a company in
Abuja, Nigeria. Bledol offers BIM construction drawings (architectural,
structural, MEP coordination, clash detection) and innovative materials
(epoxy flooring, epoxy countertops, foam concrete, solar glass panels,
aluminum honeycomb wall panels).

Rules:
- Tone: professional, confident, clear. No slang, no hype words.
- Use ONLY the facts in the project note. Never invent numbers, clients,
  locations or results.
- End with a short call to action: message us for a quote, or visit bledol.com.
- Do not use emojis.
"""


def ask_gemini(prompt):
    key = os.getenv("GEMINI_API_KEY")
    for model in MODELS:
        for attempt in range(1, 4):
            try:
                response = requests.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                    headers={"x-goog-api-key": key},
                    json={"contents": [{"parts": [{"text": prompt}]}]},
                    timeout=90,
                )
            except requests.exceptions.RequestException:
                time.sleep(5 * attempt)
                continue
            if response.status_code == 200:
                data = response.json()
                return data["candidates"][0]["content"]["parts"][0]["text"].strip()
            if response.status_code in (429, 500, 503):
                time.sleep(5 * attempt)
            else:
                raise RuntimeError(f"Gemini error {response.status_code}: {response.text[:200]}")
    raise RuntimeError("Gemini is busy. Try again in a few minutes.")


def write_posts(project_note):
    prompt = (
        BRAND_GUIDE
        + "\nProject note:\n"
        + project_note
        + "\n\nWrite two versions, in exactly this format:\n"
        + "INSTAGRAM:\n(max 60 words, then 3 to 5 hashtags)\n"
        + "FACEBOOK:\n(max 100 words, no hashtags)\n"
    )
    text = ask_gemini(prompt)
    if "FACEBOOK:" in text:
        instagram, facebook = text.split("FACEBOOK:", 1)
        instagram = instagram.replace("INSTAGRAM:", "").strip()
        return {"instagram": instagram, "facebook": facebook.strip()}
    return {"instagram": text, "facebook": text}


if __name__ == "__main__":
    note = (
        "Epoxy floor installation, commercial warehouse in Idu, Abuja. "
        "High-gloss industrial finish. Completed in 3 weeks."
    )
    posts = write_posts(note)
    print("--- INSTAGRAM ---")
    print(posts["instagram"])
    print("\n--- FACEBOOK ---")
    print(posts["facebook"])