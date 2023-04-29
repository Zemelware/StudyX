import os

import requests
from dotenv import load_dotenv

load_dotenv()

url = "http://localhost:5001/upload-audio"
api_key = os.getenv("CLIENT_API_KEY")

with open("recording_og.wav", "rb") as f:
    response = requests.post(url, headers={"api-key": api_key},
                             files={"recording": f})
