import sys
from pathlib import Path
from dotenv import load_dotenv
import os
import pg8000
import urllib.parse

# Add root to path
sys.path.insert(0, str(Path.cwd()))

# Load .env
load_dotenv()

def init():
    print("Reading schema.sql...")
    schema_path = Path("schema.sql")
    if not schema_path.exists():
        print("schema.sql not found!")
        return
    
    with open(schema_path, "r", encoding="utf-8") as f:
        sql_content = f.read()

    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL not found!")
        return

    url = db_url.replace("postgres://", "postgresql://")
    result = urllib.parse.urlparse(url)
    
    print("Connecting to Supabase...")
    conn = pg8000.connect(
        user=result.username,
        password=result.password,
        host=result.hostname,
        port=result.port or 5432,
        database=result.path.lstrip('/'),
        ssl_context=True
    )
    cur = conn.cursor()

    print("Dropping existing tables to ensure clean schema...")
    tables_to_drop = [
        'metrics', 
        'manychat_interactions', 
        'sync_logs', 
        'manychat_automations', 
        'manychat_pings', 
        'youtube_videos', 
        'instagram_media', 
        'users'
    ]
    for t in tables_to_drop:
        try:
            print(f"  - Dropping public.{t}...")
            cur.execute(f'DROP TABLE IF EXISTS public.{t} CASCADE')
            conn.commit()
        except Exception as e:
            print(f"  - Error dropping {t}: {e}")
            conn.rollback()

    cur = conn.cursor() # Fresh cursor
    print("Executing schema.sql...")
    # Split by semicolon and execute
    # We use a simple split; this might fail if semicolons are in strings, 
    # but schema.sql is simple.
    statements = sql_content.split(";")
    for stmt in statements:
        stmt = stmt.strip()
        if not stmt:
            continue
        try:
            print(f"Executing statement starting with: {stmt[:50]}...")
            cur.execute(stmt)
            conn.commit()
        except Exception as e:
            print(f"Error executing statement: {e}")
            conn.rollback()
    
    conn.close()
    print("Schema initialization with schema.sql complete.")

if __name__ == "__main__":
    init()
