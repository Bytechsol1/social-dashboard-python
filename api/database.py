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
            
            conn = pg8000.connect(
                user=result.username,
                password=result.password,
                host=result.hostname,
                port=result.port or 5432,
                database=result.path.lstrip('/'),
                ssl_context=True if "supabase" in db_url or "neon" in db_url else None
            )
            return PostgresWrapper(conn)
        except Exception as e:
            print(f"[DB ERROR] Postgres failed: {e}. Falling back...")

    try:
        # On Vercel, we MUST NOT attempt to connect if the file doesn't exist,
        # otherwise SQLite will try to create it and crash with "Read-only file system".
        if is_vercel and not DB_PATH.exists():
             print(f"[DB INFO] {DB_PATH} not found. Forcing fallback.")
             raise sqlite3.OperationalError("Database file missing on read-only FS")

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
            
            # CRITICAL: Since :memory: DBs are connection-isolated, we MUST
            # initialize the schema for every new connection in this mode.
            _init_schema(conn)
            return conn
        raise

@contextmanager
def get_db():
    """Context manager for SQLite connections with auto-commit/close."""
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
    """Internal helper to shared schema logic without recursion."""
    # Detect if we are using Postgres or SQLite
    is_postgres = hasattr(conn, "conn") and conn.__class__.__name__ == "PostgresWrapper"
    
    # SQLite uses AUTOINCREMENT, Postgres uses SERIAL
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
        CREATE TABLE IF NOT EXISTS manychat_pings (
            id {id_type},
            user_id TEXT,
            automation_id TEXT,
            type TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
    """)
    # Run migrations on this conn as well
    _safe_migrate_conn(conn)

def init_db():
    """Create all tables if they don't exist (called on startup)."""
    with get_db() as conn:
        _init_schema(conn)
        # Only run ad-hoc migrations on SQLite. 
        # Postgres schema should be managed via schema.sql
        if get_storage_engine() == "sqlite":
            _safe_migrate_conn(conn)

def _safe_migrate():
    if get_storage_engine() == "sqlite":
        with get_db() as conn:
            _safe_migrate_conn(conn)

def _safe_migrate_conn(conn: sqlite3.Connection):
    """Add new columns to existing tables without dropping data."""
    migrations = [
        ("users",                  "youtube_channel_id", "TEXT"),
        ("sync_logs",              "flow_id",            "TEXT"),
        ("manychat_automations",   "synced_at",          "TIMESTAMP"),
        ("manychat_automations",   "clicks",             "INTEGER DEFAULT 0"),
        ("users",                  "ig_access_token",     "TEXT"),
        ("users",                  "ig_user_id",          "TEXT"),
        ("users",                  "ig_audience_json",    "TEXT"),
    ]
    for table, column, col_type in migrations:
        try:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
            print(f"[DB MIGRATE] Added {table}.{column}")
        except Exception:
            pass  # Column already exists
