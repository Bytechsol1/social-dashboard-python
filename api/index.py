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
from fastapi.responses import JSONResponse

# Avoid heavy top-level imports to prevent Vercel Cold Start timeouts
# Routers and DB will be imported locally or later in the file

app = FastAPI(title="Social Intelligence Dashboard API", version="2.0.0")

# Allow Vite dev server (port 3000) to hit the API
# Allow both local dev and production domains
# Using '*' for origins on Vercel is often necessary initially to debug connectivity
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

@app.get("/api/health")
def health_check():
    """Diagnostic route to verify server is up without DB access."""
    return {"status": "healthy", "service": "api"}

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

# Initialize SQLite schema lazily — we don't use @app.on_event("startup") 
# as it can cause timeouts on Vercel Hobby tier.

# DEFERRED ROUTER INCLUSION
try:
    from api.routes.api import router as api_router
    from api.routes.debug import router as debug_router
except ImportError:
    from routes.api import router as api_router
    from routes.debug import router as debug_router

# Include routers with and without prefix for Vercel/Local compatibility
app.include_router(api_router, prefix="/api")
app.include_router(debug_router, prefix="/api/debug")

# Vercel fallback: some environments pass the path WITHOUT the /api prefix 
# after the rewrite. This ensures those requests still hit the right handlers.
app.include_router(api_router)
app.include_router(debug_router, prefix="/debug")

if __name__ == "__main__":
    import uvicorn
    import sys
    from pathlib import Path

    # Add parent dir to sys.path so 'api' can be found when running directly
    sys.path.insert(0, str(Path(__file__).parent.parent))
    uvicorn.run("api.index:app", host="0.0.0.0", port=8000, reload=True)
