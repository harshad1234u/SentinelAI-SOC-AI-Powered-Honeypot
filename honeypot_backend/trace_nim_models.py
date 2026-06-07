import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.environ.get("NIM_API_KEY")

headers = {
    "Authorization": f"Bearer {api_key}",
    "Accept": "application/json"
}

resp = requests.get("https://integrate.api.nvidia.com/v1/models", headers=headers)
models = resp.json()

for model in models.get("data", []):
    print(model.get("id"))
