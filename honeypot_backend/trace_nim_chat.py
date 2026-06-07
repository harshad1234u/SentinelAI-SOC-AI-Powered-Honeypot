import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.environ.get("NIM_API_KEY")

headers = {
    "Authorization": f"Bearer {api_key}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

payload = {
    "model": "meta/llama-3.1-70b-instruct",
    "messages": [
        {"role": "user", "content": "Hello"}
    ],
    "max_tokens": 10
}

resp = requests.post("https://integrate.api.nvidia.com/v1/chat/completions", headers=headers, json=payload)
print(resp.status_code)
print(resp.text)
