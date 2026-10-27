import os
import requests
from dotenv import load_dotenv

load_dotenv()

GRAPH = "https://graph.facebook.com/v26.0"
ig_id = os.getenv("IG_USER_ID")
token = os.getenv("PAGE_TOKEN")

response = requests.get(
    f"{GRAPH}/{ig_id}",
    params={"fields": "username,followers_count,media_count", "access_token": token},
    timeout=30,
)

print(response.json())