
import asyncio
import os
import sqlite3
from dotenv import load_dotenv
from api.services.sync_engine import perform_sync

# Load environment variables from .env
load_dotenv()

async def main():
    user_id = "134acfd2-cb6e-4356-81d9-32457fc555de"
    print(f"Triggering sync for {user_id}...")
    result = await perform_sync(user_id)
    print(f"Sync Result: {result}")

if __name__ == "__main__":
    asyncio.run(main())
