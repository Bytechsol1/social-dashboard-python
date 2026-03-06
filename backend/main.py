"""FastAPI application entry point."""
import os
from dotenv import load_dotenv

# Load .env before anything else
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database import init_db
from backend.routes.api import router as api_router
from backend.routes.debug import router as debug_router

app = FastAPI(title="Social Intelligence Dashboard API", version="2.0.0")

# Allow Vite dev server (port 3000) to hit the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        os.environ.get("APP_URL", "http://localhost:3000"),
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "Social Intelligence Backend",
        "api_docs": "/docs",
        "api_root": "/api/dashboard"
    }

# Initialize SQLite schema on startup (includes safe migrations)
@app.on_event("startup")
def startup():
    init_db()
    print("[STARTUP] Database initialized with latest schema migrations.")

# Mount all routes
app.include_router(api_router, prefix="/api")
app.include_router(debug_router, prefix="/api/debug")

if __name__ == "__main__":
    import uvicorn
    import sys
    from pathlib import Path

    # Add parent dir to sys.path so 'backend' can be found when running directly
    sys.path.insert(0, str(Path(__file__).parent.parent))
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
