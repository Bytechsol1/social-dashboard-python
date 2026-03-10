
import asyncio
import os
import sqlite3
import json
from dotenv import load_dotenv
from api.services.sync_engine import perform_sync

# Load environment variables from .env
load_dotenv()

async def debug_sync():
    user_id = "134acfd2-cb6e-4356-81d9-32457fc555de"
    db_path = 'social_intel.db'
    
    print(f"--- PRE-SYNC AUDIT for {user_id} ---")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if user:
        user_dict = dict(user)
        print(f"User found: {user_dict['id']}")
        print(f"IG Access Token (stored) exists: {bool(user_dict.get('ig_access_token'))}")
        print(f"IG User ID (stored): {user_dict.get('ig_user_id')}")
    else:
        print("User NOT found in DB!")
    
    env_token = os.environ.get("INSTAGRAM_ACCESS_TOKEN")
    print(f"INSTAGRAM_ACCESS_TOKEN in env: {bool(env_token)} (Starts with: {env_token[:10] if env_token else 'N/A'})")
    
    conn.close()
    
    print(f"\n--- TRIGGERING SYNC ---")
    result = await perform_sync(user_id)
    print(f"Sync Result: {result}")
    
    print(f"\n--- POST-SYNC AUDIT ---")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT metric_name, value, date FROM metrics WHERE user_id = ? AND source = 'instagram' ORDER BY date DESC", (user_id,))
    rows = cur.fetchall()
    print(f"Instagram metrics count: {len(rows)}")
    for r in rows:
        print(f"  {r['metric_name']}: {r['value']} ({r['date']})")
    conn.close()

if __name__ == "__main__":
    asyncio.run(debug_sync())
