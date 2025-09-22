
import requests

API_URL = "https://your-api-url-here"

offers = [
    {"sku": "starter-001", "name": "Starter Offer", "description": "Entry level plan", "price": 19},
    {"sku": "pro-001", "name": "Pro Offer", "description": "Advanced plan with extra features", "price": 79}
]

for offer in offers:
    response = requests.post(f"{API_URL}/offers", json=offer)
    print(f"Offer {offer['sku']} status: {response.status_code}")
