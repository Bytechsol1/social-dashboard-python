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

class PostgresWrapper:
    """Minimal shim to make Postgres look like SQLite (row_factory, executescript)."""
    def __init__(self, conn):
        self.conn = conn
    
    def cursor(self):
        return self.conn.cursor()

    def execute(self, sql, params=None):
        # Translate SQLite ? to Postgres %s
        sql = sql.replace("?", "%s")
        # Handle 'ON CONFLICT' syntax differences if necessary, 
        # but for now we'll stick to basic SQL or use try/except.
        cur = self.conn.cursor()
        cur.execute(sql, params)
        return cur

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

def get_connection() -> sqlite3.Connection:
    """Return a new SQLite connection with row_factory set.
    Optimized for Vercel/stateless environments.
    """
    is_vercel = os.environ.get("VERCEL") == "1"
    
    db_url = os.environ.get("DATABASE_URL")
    if db_url:
        try:
            import pg8000
            # Parse connection string
            # Handle 'postgres://' vs 'postgresql://' for different providers
            db_url = db_url.replace("postgres://", "postgresql://")
            conn = pg8000.connect(dsn=db_url)
            # Add a row_factory equivalent
            # In pg8000 we can use a custom column factory but for simplicity we wrap it
            return PostgresWrapper(conn)
        except Exception as e:
            print(f"[DB ERROR] Failed to connect to Postgres: {e}")
            # Fallback to sqlite (memory)
            pass

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
