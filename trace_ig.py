import os
import httpx
from dotenv import load_dotenv
load_dotenv()

token = os.environ.get("INSTAGRAM_ACCESS_TOKEN")
print(f"Token (first 10 chars): {token[:10] if token else 'None'}")

if token:
    with httpx.Client() as client:
        # Step 1: Get Pages
        res = client.get("https://graph.facebook.com/v19.0/me/accounts", params={"access_token": token})
        print(f"Pages status: {res.status_code}")
        print(f"Pages Body: {res.text}")
        
        data = res.json()
        if "data" in data:
            for page in data["data"]:
                page_id = page["id"]
                # Step 2: Get IG account for each page
                res_ig = client.get(f"https://graph.facebook.com/v19.0/{page_id}", params={"fields": "instagram_business_account", "access_token": token})
                print(f"Page {page_id} IG status: {res_ig.status_code}")
                print(f"Page {page_id} IG Body: {res_ig.text}")
else:
    print("No token found in .env")
