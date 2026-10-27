import os
import requests
from dotenv import load_dotenv

load_dotenv()

cloud = os.getenv("CLOUDINARY_CLOUD_NAME")
key = os.getenv("CLOUDINARY_API_KEY")
secret = os.getenv("CLOUDINARY_API_SECRET")

response = requests.get(
    f"https://api.cloudinary.com/v1_1/{cloud}/ping",
    auth=(key, secret),
    timeout=30,
)

print(response.status_code, response.json())