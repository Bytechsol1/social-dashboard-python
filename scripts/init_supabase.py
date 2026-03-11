import sys
from pathlib import Path
from dotenv import load_dotenv
import os

# Add root to path
sys.path.insert(0, str(Path.cwd()))

# Load .env
load_dotenv()

print(f"DATABASE_URL is set: {bool(os.environ.get('DATABASE_URL'))}")

from api.database import init_db

print("Starting init_db()...")
init_db()
print("Database schema initialization complete.")
