import sys
from pathlib import Path
from dotenv import load_dotenv
import os

# Add root to path
sys.path.insert(0, str(Path.cwd()))

# Load .env
load_dotenv()

from api.database import get_connection, init_db

def recreate():
    print("Connecting to Supabase...")
    conn = get_connection()
    cur = conn.cursor()
    
    tables = [
        'metrics', 
        'manychat_interactions', 
        'sync_logs', 
        'manychat_automations', 
        'manychat_pings', 
        'youtube_videos', 
        'instagram_media', 
        'users'
    ]
    
    print("Dropping tables...")
    for t in tables:
        try:
            cur.execute(f'DROP TABLE IF EXISTS public.{t} CASCADE')
            print(f"  - Dropped public.{t}")
        except Exception as e:
            print(f"  - Error dropping {t}: {e}")
            conn.rollback()
            cur = conn.cursor() # Get a fresh cursor after rollback
    
    conn.commit()
    conn.close()
    
    print("Re-initializing schema...")
    init_db()
    print("Schema re-initialized successfully.")

if __name__ == "__main__":
    recreate()
