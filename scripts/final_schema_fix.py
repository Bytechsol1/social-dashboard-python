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

def fix():
    db_url = os.environ.get("DATABASE_URL")
    url = db_url.replace("postgres://", "postgresql://")
    result = urllib.parse.urlparse(url)
    
    conn = pg8000.connect(
        user=result.username,
        password=result.password,
        host=result.hostname,
        port=result.port or 5432,
        database=result.path.lstrip('/'),
        ssl_context=True
    )
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
    
    print("Dropping and Creating tables in public schema...")
    
    # metrics
    cur.execute("DROP TABLE IF EXISTS public.metrics CASCADE")
    # manychat_interactions
    cur.execute("DROP TABLE IF EXISTS public.manychat_interactions CASCADE")
    # sync_logs
    cur.execute("DROP TABLE IF EXISTS public.sync_logs CASCADE")
    # manychat_automations
    cur.execute("DROP TABLE IF EXISTS public.manychat_automations CASCADE")
    # manychat_pings
    cur.execute("DROP TABLE IF EXISTS public.manychat_pings CASCADE")
    # youtube_videos
    cur.execute("DROP TABLE IF EXISTS public.youtube_videos CASCADE")
    # instagram_media
    cur.execute("DROP TABLE IF EXISTS public.instagram_media CASCADE")
    # users (LAST because of FKs)
    cur.execute("DROP TABLE IF EXISTS public.users CASCADE")
    conn.commit()

    print("Recreating public.users...")
    cur.execute("""
        CREATE TABLE public.users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE,
            yt_refresh_token TEXT,
            manychat_key TEXT,
            youtube_channel_id TEXT,
            ig_access_token TEXT,
            ig_user_id TEXT,
            ig_audience_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    print("Recreating other tables...")
    cur.execute("""
        CREATE TABLE public.metrics (
            id TEXT PRIMARY KEY,
            user_id TEXT REFERENCES public.users(id) ON DELETE CASCADE,
            date TEXT,
            source TEXT,
            metric_name TEXT,
            dimension TEXT DEFAULT 'none',
            value REAL,
            UNIQUE(user_id, date, source, metric_name, dimension)
        )
    """)
    cur.execute("""
        CREATE TABLE public.manychat_interactions (
            id TEXT PRIMARY KEY,
            user_id TEXT REFERENCES public.users(id) ON DELETE CASCADE,
            subscriber_id TEXT,
            type TEXT,
            details TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute("""
        CREATE TABLE public.sync_logs (
            id SERIAL PRIMARY KEY,
            user_id TEXT REFERENCES public.users(id) ON DELETE CASCADE,
            status TEXT,
            message TEXT,
            flow_id TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute("""
        CREATE TABLE public.manychat_automations (
            id TEXT PRIMARY KEY,
            user_id TEXT REFERENCES public.users(id) ON DELETE CASCADE,
            name TEXT,
            status TEXT,
            runs INTEGER DEFAULT 0,
            clicks INTEGER DEFAULT 0,
            ctr REAL DEFAULT 0,
            last_modified TEXT,
            synced_at TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute("""
        CREATE TABLE public.manychat_pings (
            id SERIAL PRIMARY KEY,
            user_id TEXT REFERENCES public.users(id) ON DELETE CASCADE,
            automation_id TEXT,
            type TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute("""
        CREATE TABLE public.youtube_videos (
            id TEXT PRIMARY KEY,
            user_id TEXT REFERENCES public.users(id) ON DELETE CASCADE,
            title TEXT,
            published_at TEXT,
            view_count INTEGER DEFAULT 0,
            like_count INTEGER DEFAULT 0,
            comment_count INTEGER DEFAULT 0,
            thumbnail_url TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute("""
        CREATE TABLE public.instagram_media (
            id TEXT PRIMARY KEY,
            user_id TEXT REFERENCES public.users(id) ON DELETE CASCADE,
            caption TEXT,
            media_type TEXT,
            media_url TEXT,
            permalink TEXT,
            timestamp TIMESTAMP,
            like_count INTEGER DEFAULT 0,
            comments_count INTEGER DEFAULT 0,
            view_count INTEGER DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()
    print("Final schema fix complete!")

if __name__ == "__main__":
    fix()
