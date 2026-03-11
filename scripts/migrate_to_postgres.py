import sqlite3
import os
import pg8000
import urllib.parse
from pathlib import Path
from dotenv import load_dotenv

# Load env vars
load_dotenv()

DB_PATH = Path("social_intel.db")
DATABASE_URL = os.environ.get("DATABASE_URL")

def get_pg_conn():
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL not found in .env")
    
    url = DATABASE_URL.replace("postgres://", "postgresql://")
    result = urllib.parse.urlparse(url)
    
    return pg8000.connect(
        user=result.username,
        password=result.password,
        host=result.hostname,
        port=result.port or 5432,
        database=result.path.lstrip('/'),
        ssl_context=True # Supabase requires SSL
    )

def migrate():
    if not DB_PATH.exists():
        print(f"SQLite DB not found at {DB_PATH}")
        return

    print(f"Connecting to SQLite: {DB_PATH}")
    sqlite_conn = sqlite3.connect(str(DB_PATH))
    sqlite_conn.row_factory = sqlite3.Row
    
    print("Connecting to Postgres...")
    pg_conn = get_pg_conn()
    pg_cursor = pg_conn.cursor()

    tables = [
        "users",
        "metrics",
        "manychat_interactions",
        "sync_logs",
        "manychat_automations",
        "manychat_pings",
        "youtube_videos",
        "instagram_media"
    ]

    for table in tables:
        print(f"Migrating table: {table}")
        
        # Get data from SQLite
        rows = sqlite_conn.execute(f"SELECT * FROM {table}").fetchall()
        if not rows:
            print(f"  - No data in {table}, skipping.")
            continue
        
        # Get columns
        columns = rows[0].keys()
        placeholders = ", ".join(["%s"] * len(columns))
        col_names = ", ".join(columns)
        
        # Insert into Postgres (Explicitly use public schema)
        insert_sql = f"INSERT INTO public.{table} ({col_names}) VALUES ({placeholders}) ON CONFLICT DO NOTHING"
        
        data_to_insert = [tuple(row) for row in rows]
        
        try:
            pg_cursor.executemany(insert_sql, data_to_insert)
            print(f"  - Migrated {len(data_to_insert)} rows.")
        except Exception as e:
            print(f"  - Error migrating {table}: {e}")
            pg_conn.rollback()
            continue

    pg_conn.commit()
    print("Migration complete!")
    sqlite_conn.close()
    pg_conn.close()

if __name__ == "__main__":
    migrate()
