"""SQLite database connection and schema initialization."""
import sqlite3
import os
from contextlib import contextmanager
from pathlib import Path
import threading

# Guard to prevent redundant schema init in same process
_schema_initialized = False
_schema_lock = threading.Lock()

# Database Configuration
# sqlite3 is used for local dev.
# For Vercel, we bridge to Postgres (Neon / Supabase) via DATABASE_URL.
DB_PATH = (Path(__file__).parent.parent / "social_intel.db").resolve()

class PostgresRow:
    """A row wrapper that allows conversion to dict, matching sqlite3.Row."""
    def __init__(self, colnames, values):
        self._data = dict(zip(colnames, values))
    
    def __getitem__(self, key):
        return self._data[key]
    
    def keys(self):
        return self._data.keys()

    def __iter__(self):
        return iter(self._data.keys())

    def get(self, key, default=None):
        return self._data.get(key, default)

class PostgresWrapper:
    """Minimal shim to make Postgres look like SQLite (row_factory, executescript)."""
    def __init__(self, conn):
        self.conn = conn
    
    def cursor(self):
        return self.conn.cursor()

    def execute(self, sql, params=None):
        # Translate SQLite ? to Postgres %s
        sql = sql.replace("?", "%s")
        cur = self.conn.cursor()
        cur.execute(sql, params or ())
        return PostgresCursorWrapper(cur)

    def executescript(self, sql):
        # Postgres doesnt have executescript, we split by semicolon
        cur = self.conn.cursor()
        for statement in sql.split(";"):
            if statement.strip():
                cur.execute(statement)
        self.conn.commit()

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def close(self):
        self.conn.close()

class PostgresCursorWrapper:
    """Wrapper for pg8000 cursor to mimic sqlite3.Row results."""
    def __init__(self, cursor):
        self.cursor = cursor
    
    def fetchone(self):
        row = self.cursor.fetchone()
        if not row: return None
        colnames = [desc[0].decode() if isinstance(desc[0], bytes) else desc[0] for desc in self.cursor.description]
        return PostgresRow(colnames, row)
    
    def fetchall(self):
        rows = self.cursor.fetchall()
        if not rows: return []
        colnames = [desc[0].decode() if isinstance(desc[0], bytes) else desc[0] for desc in self.cursor.description]
        return [PostgresRow(colnames, r) for r in rows]

def get_storage_engine() -> str:
    """Diagnostics helper to see what DB we are actually using."""
    db_url = os.environ.get("DATABASE_URL")
    if db_url: return "postgres"
    if os.environ.get("VERCEL") == "1": return "sqlite_memory"
    return "sqlite_disk"

def get_connection():
    """Return a new SQLite or Postgres connection.
    Hardened for Vercel/stateless environments.
    """
    is_vercel = os.environ.get("VERCEL") == "1"
    db_url = os.environ.get("DATABASE_URL")

    if db_url:
        try:
            import pg8000
            import urllib.parse
            
            # Robust parsing for complex passwords
            db_url = db_url.replace("postgres://", "postgresql://")
            result = urllib.parse.urlparse(db_url)
            
            # Force IPv4 resolution to prevent Errno 99 on Vercel
            import socket
            target_host = result.hostname
            try:
                ipv4_addresses = socket.getaddrinfo(result.hostname, result.port or 5432, family=socket.AF_INET)
                if ipv4_addresses:
                    target_host = ipv4_addresses[0][4][0]
            except Exception:
                pass # Fallback to original hostname if IPv4 resolution fails

            # Helper to create connection with optional port override
            def _connect(port):
                return pg8000.connect(
                    user=result.username,
                    password=result.password,
                    host=target_host,
                    port=port,
                    database=result.path.lstrip('/'),
                    timeout=20,
                    ssl_context=True if db_url and ("supabase" in db_url or "neon" in db_url) else None
                )

            try:
                conn = _connect(result.port or 5432)
            except Exception as e:
                # If direct port fails and it's Supabase, try the connection pooler port (6543)
                hostname = result.hostname or ""
                if "supabase.co" in hostname and (not result.port or result.port == 5432):
                    conn = _connect(6543)
                else:
                    raise e

            return PostgresWrapper(conn)
        except Exception as e:
            import traceback
            print(f"[DB ERROR] Postgres connection failed: {e}")
            if is_vercel:
                raise Exception(f"Postgres connection failed: {str(e)}\n{traceback.format_exc()}")

    try:
        # SQLite logic
        if is_vercel and not DB_PATH.exists():
             raise sqlite3.OperationalError("Database file missing on read-only FS")

        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        if not is_vercel:
            try: conn.execute("PRAGMA journal_mode=WAL")
            except Exception: pass
        conn.execute("PRAGMA foreign_keys=ON")
        return conn
    except sqlite3.Error as e:
        if is_vercel:
            conn = sqlite3.connect(":memory:")
            conn.row_factory = sqlite3.Row
            _init_schema(conn)
            return conn
        raise

@contextmanager
def get_db():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def _init_schema(conn):
    is_postgres = hasattr(conn, "conn") and conn.__class__.__name__ == "PostgresWrapper"
    id_type = "SERIAL PRIMARY KEY" if is_postgres else "INTEGER PRIMARY KEY AUTOINCREMENT"
    
    conn.executescript(f"""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE,
            yt_refresh_token TEXT,
            manychat_key TEXT,
            youtube_channel_id TEXT,
            ig_access_token TEXT,
            ig_user_id TEXT,
            ig_audience_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS sync_logs (
            id {id_type},
            user_id TEXT,
            status TEXT,
            message TEXT,
            flow_id TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
            synced_at TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS instagram_media (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            caption TEXT,
            media_type TEXT,
            media_url TEXT,
            permalink TEXT,
            timestamp TIMESTAMP,
            like_count INTEGER DEFAULT 0,
            comments_count INTEGER DEFAULT 0,
            view_count INTEGER DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS youtube_ideas (
            id {id_type},
            user_id TEXT,
            title TEXT,
            description TEXT,
            suggested_month_year TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS youtube_shorts_suggestions (
            id {id_type},
            user_id TEXT,
            video_id TEXT,
            start_time TEXT,
            stop_time TEXT,
            reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    if is_postgres:
        try:
            conn.execute("SELECT setval('sync_logs_id_seq', (SELECT COALESCE(MAX(id), 0) + 1 FROM sync_logs), false)")
        except Exception: pass

    _safe_migrate_conn(conn)

def init_db():
    with get_db() as conn:
        _init_schema(conn)

def _safe_migrate_conn(conn):
    migrations = [
        ("users", "youtube_channel_id", "TEXT"),
        ("sync_logs", "flow_id", "TEXT"),
        ("manychat_automations", "synced_at", "TIMESTAMP"),
        ("manychat_automations", "clicks", "INTEGER DEFAULT 0"),
        ("users", "ig_access_token", "TEXT"),
        ("users", "ig_user_id", "TEXT"),
        ("users", "ig_audience_json", "TEXT"),
    ]
    for table, column, col_type in migrations:
        try:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
        except Exception: pass
