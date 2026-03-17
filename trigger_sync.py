import asyncio
import os
from api.services.sync_engine import perform_sync
from dotenv import load_dotenv

load_dotenv()

async def main():
    user_id = os.environ.get("VITE_DEMO_USER_ID") or "default_user"
    print(f"Triggering sync for {user_id}...")
    results = await perform_sync(user_id)
    print("Sync Results:", results)

if __name__ == "__main__":
    asyncio.run(main())
