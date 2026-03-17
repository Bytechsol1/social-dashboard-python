import os
from dotenv import load_dotenv
load_dotenv()

from api.database import init_db

# Set demo user ID if not set
if not os.environ.get("VITE_DEMO_USER_ID"):
    os.environ["VITE_DEMO_USER_ID"] = "134acfd2-cb6e-4356-81d9-32457fc555de"

print("Force running init_db with .env loaded...")
init_db()
print("Done.")
