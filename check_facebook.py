import os
import requests
from dotenv import load_dotenv

load_dotenv()

GRAPH = "https://graph.facebook.com/v26.0"
page_id = os.getenv("PAGE_ID")
token = os.getenv("PAGE_TOKEN")

response = requests.get(
    f"{GRAPH}/{page_id}",
    params={"fields": "name,id", "access_token": token},
    timeout=30,
)

print(response.json())