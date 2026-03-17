import asyncio
import os
from dotenv import load_dotenv
load_dotenv()

from api.services.sync_engine import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, perform_sync

async def main():
    print(f"DEBUG: GOOGLE_CLIENT_ID='{GOOGLE_CLIENT_ID}'")
    print(f"DEBUG: GOOGLE_CLIENT_SECRET='{GOOGLE_CLIENT_SECRET}'")
    
    user_id = os.environ.get("VITE_DEMO_USER_ID") or "default_user"
    print(f"Triggering sync for {user_id}...")
    results = await perform_sync(user_id)
    print("Sync Results:", results)

if __name__ == "__main__":
    asyncio.run(main())
