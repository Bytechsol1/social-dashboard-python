"""SQLite database connection and schema initialization."""
import sqlite3
import os
from contextlib import contextmanager
from pathlib import Path

# Database file lives at project root
# Using .resolve() ensures we find the actual file on Vercel
DB_PATH = (Path(__file__).parent.parent / "social_intel.db").resolve()

def get_connection() -> sqlite3.Connection:
    """Return a new SQLite connection with row_factory set.
    Optimized for Vercel/stateless environments.
    """
    is_vercel = os.environ.get("VERCEL") == "1"
    
    # Check for DATABASE_URL (for hosted Postgres/Neon/Supabase)
    if os.environ.get("DATABASE_URL"):
        # Future: Switch to Postgres. For now, we still use SQLite.
        pass

    try:
        # On Vercel, if DB doesn't exist, this fails because filesystem is read-only
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        
        # WAL mode is not supported on Vercel's read-only filesystem
        if not is_vercel:
            try:
                conn.execute("PRAGMA journal_mode=WAL")
            except Exception:
                pass
        
        conn.execute("PRAGMA foreign_keys=ON")
        return conn
    except sqlite3.Error as e:
        print(f"[DB ERROR] Could not connect to {DB_PATH}: {e}")
        if is_vercel:
            print("[DB INFO] Falling back to :memory: database (Stateless/Ephemeral)")
            conn = sqlite3.connect(":memory:")
            conn.row_factory = sqlite3.Row
            # CRITICAL: If in-memory, we MUST init the schema immediately for this lifecycle
            _init_schema(conn)
            return conn
        raise

def _init_schema(conn: sqlite3.Connection):
    """Internal helper to shared schema logic without recursion."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE,
            yt_refresh_token TEXT,
            manychat_key TEXT,
            youtube_channel_id TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS metrics (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            date TEXT,
            source TEXT,
            metric_name TEXT,
            dimension TEXT DEFAULT 'none',
            value REAL,
            UNIQUE(user_id, date, source, metric_name, dimension)
        );
        CREATE TABLE IF NOT EXISTS manychat_interactions (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            subscriber_id TEXT,
            type TEXT,
            details TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS sync_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            status TEXT,
            message TEXT,
            flow_id TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS manychat_automations (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            name TEXT,
            status TEXT,
            runs INTEGER DEFAULT 0,
            clicks INTEGER DEFAULT 0,
            ctr REAL DEFAULT 0,
            last_modified TEXT,
            synced_at DATETIME,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS manychat_pings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            automation_id TEXT,
            type TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS youtube_videos (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            title TEXT,
            published_at TEXT,
            view_count INTEGER DEFAULT 0,
            like_count INTEGER DEFAULT 0,
            comment_count INTEGER DEFAULT 0,
            thumbnail_url TEXT,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)
    # Run migrations on this conn as well
    _safe_migrate_conn(conn)

def init_db():
    """Create all tables if they don't exist (called on startup)."""
    with get_db() as conn:
        _init_schema(conn)

def _safe_migrate():
    with get_db() as conn:
        _safe_migrate_conn(conn)

def _safe_migrate_conn(conn: sqlite3.Connection):
    """Add new columns to existing tables without dropping data."""
    migrations = [
        ("users",                  "youtube_channel_id", "TEXT"),
        ("sync_logs",              "flow_id",            "TEXT"),
        ("manychat_automations",   "synced_at",          "DATETIME"),
        ("manychat_automations",   "clicks",             "INTEGER DEFAULT 0"),
    ]
    for table, column, col_type in migrations:
        try:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
            print(f"[DB MIGRATE] Added {table}.{column}")
        except Exception:
            pass  # Column already exists
