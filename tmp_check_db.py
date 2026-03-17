import sqlite3
import os
from api.database import DB_PATH

if not os.path.exists(DB_PATH):
    print(f"Database not found at {DB_PATH}")
else:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    user = conn.execute("SELECT id, ig_access_token, ig_user_id FROM users").fetchone()
    if user:
        print(f"User ID: {user['id']}")
        print(f"Token: {'Set' if user['ig_access_token'] else 'Not set'}")
        print(f"IG ID: {user['ig_user_id']}")
    else:
        print("No users found")
    conn.close()
