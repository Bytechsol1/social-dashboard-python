# Legacy Shim for Vercel
# This catches any old project settings still looking for backend/main.py
import sys
from pathlib import Path

# Add 'api' to sys.path so we can import the new entry point
api_dir = (Path(__file__).parent.parent / "api").resolve()
if str(api_dir) not in sys.path:
    sys.path.insert(0, str(api_dir))

# Proxy all requests to the new index.py FASTAPI app
from index import app
