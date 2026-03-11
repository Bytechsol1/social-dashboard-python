import sys
from pathlib import Path

# Hardened path patching for Vercel
api_dir = Path(__file__).parent.resolve()
root_dir = api_dir.parent.resolve()
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))
if str(api_dir) not in sys.path:
    sys.path.insert(0, str(api_dir))

import os
from dotenv import load_dotenv

# Load .env before anything else
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Social Intelligence Dashboard API", version="2.0.0")

# Allow Vite dev server (port 3000) to hit the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if os.environ.get("VERCEL") else [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        os.environ.get("APP_URL", "http://localhost:3000"),
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Exception Handler to capture 500 errors on Vercel
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    import traceback
    error_details = traceback.format_exc()
    print(f"[FATAL ERROR] {error_details}")
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": str(exc),
            "traceback": error_details if os.environ.get("VERCEL") else None
        }
    )

# Router and Route Initialization
BOOT_ERROR = None
api_router = None
debug_router = None

try:
    # ── Router Inclusion ────────────────────────────────────────────────────────
    try:
        from api.routes.api import router as _api_router
        from api.routes.debug import router as _debug_router
        api_router = _api_router
        debug_router = _debug_router
    except ImportError:
        from routes.api import router as _api_router
        from routes.debug import router as _debug_router
        api_router = _api_router
        debug_router = _debug_router

    # Include routers
    app.include_router(api_router, prefix="/api")
    app.include_router(debug_router, prefix="/api/debug")

    # ── Static File Serving (For Docker/Standalone/Vercel) ──────────────────
    dist_path = Path("dist")
    if dist_path.exists():
        app.mount("/assets", StaticFiles(directory=dist_path / "assets"), name="assets")
        
        @app.get("/{full_path:path}")
        async def serve_spa(full_path: str):
            # If it's not an API call, serve the index.html
            if full_path.startswith("api"):
                return JSONResponse(status_code=404, content={"detail": "Not Found"})
            return FileResponse(dist_path / "index.html")
    else:
        print("[BOOT] 'dist' folder not found. Frontend will not be served by Python.")

except Exception as e:
    import traceback
    BOOT_ERROR = traceback.format_exc()
    print(f"[BOOT FATAL] {BOOT_ERROR}")

@app.on_event("startup")
def on_startup():
    """Ensure DB schema is initialized on startup."""
    try:
        from api.database import init_db
        init_db()
        print("[BOOT] Database initialized successfully.")
    except Exception as e:
        print(f"[BOOT ERROR] Database initialization failed: {e}")

@app.get("/api/health")
def health_check():
    """Diagnostic route to verify server is up and DB is connected."""
    from api.database import get_storage_engine
    
    status = "healthy"
    if BOOT_ERROR:
        status = "boot_failure"
    
    return {
        "status": status,
        "service": "api",
        "routers_loaded": api_router is not None,
        "storage": get_storage_engine() if not BOOT_ERROR else "unknown",
        "error": BOOT_ERROR
    }

if __name__ == "__main__":
    import uvicorn
    sys.path.insert(0, str(Path(__file__).parent.parent))
    uvicorn.run("api.index:app", host="0.0.0.0", port=8000, reload=True)
