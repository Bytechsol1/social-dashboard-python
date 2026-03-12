import sys
from pathlib import Path
import os

# Add the project root and api directory to sys.path
root_dir = Path(__file__).parent.parent.resolve()
api_dir = (root_dir / "api").resolve()
sys.path.insert(0, str(root_dir))
sys.path.insert(0, str(api_dir))

from api.database import init_db, get_storage_engine, get_db

def verify_db():
    print(f"Current Storage Engine: {get_storage_engine()}")
    try:
        init_db()
        print("Database initialized successfully.")
        
        with get_db() as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            print(f"Tables in DB: {[table['name'] for table in tables]}")
            
    except Exception as e:
        print(f"Error during DB verification: {e}")

if __name__ == "__main__":
    verify_db()
