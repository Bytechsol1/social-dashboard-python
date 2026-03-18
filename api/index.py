import sys
import os
from pathlib import Path

# ── Path Setup for Vercel Serverless ──────────────────────────────
api_dir = Path(__file__).parent.resolve()
root_dir = api_dir.parent.resolve()
for p in [str(root_dir), str(api_dir)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Social Intelligence Dashboard API", version="2.0.0")

# ── CORS ──────────────────────────────────────────────────────────
IS_VERCEL = bool(os.environ.get("VERCEL"))
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Global Error Handler ───────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    import traceback
    tb = traceback.format_exc()
    print(f"[FATAL ERROR] {tb}")
    return JSONResponse(
        status_code=500,
        content={"status": "error", "message": str(exc), "traceback": tb}
    )

# ── Health Check ───────────────────────────────────────────────────
@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "vercel": IS_VERCEL,
        "python": sys.version,
        "db": os.environ.get("DATABASE_URL", "not-set")[:30] + "..." if os.environ.get("DATABASE_URL") else "sqlite"
    }

# ── Boot Error Tracking ────────────────────────────────────────────
BOOT_ERROR = None

# ── Routers ───────────────────────────────────────────────────────
try:
    try:
        from api.routes.api import router as api_router
        from api.routes.debug import router as debug_router
    except ImportError:
        from routes.api import router as api_router
        from routes.debug import router as debug_router

    app.include_router(api_router, prefix="/api")
    app.include_router(debug_router, prefix="/api/debug")
    print("[BOOT] Routers loaded successfully.")

except Exception as e:
    import traceback
    BOOT_ERROR = traceback.format_exc()
    print(f"[BOOT FATAL] Router loading failed:\n{BOOT_ERROR}")

    @app.get("/api/boot-error")
    def show_boot_error():
        return {"error": BOOT_ERROR}

# ── Static Files (local/Docker only, Vercel serves dist via @vercel/static-build) ──
if not IS_VERCEL:
    dist_path = root_dir / "dist"
    if dist_path.exists():
        app.mount("/assets", StaticFiles(directory=dist_path / "assets"), name="assets")

        @app.get("/{full_path:path}")
        async def serve_spa(full_path: str):
            if full_path.startswith("api"):
                return JSONResponse(status_code=404, content={"detail": "Not found"})
            return FileResponse(dist_path / "index.html")
    else:
        print("[BOOT] 'dist' folder not found — frontend not served by Python.")

# ── Startup ───────────────────────────────────────────────────────
@app.on_event("startup")
def on_startup():
    try:
        try:
            from api.database import init_db
        except ImportError:
            from database import init_db
        init_db()
        print("[BOOT] Database initialized.")
    except Exception as e:
        print(f"[BOOT ERROR] Database init failed: {e}")
        # Do NOT crash — routes must still respond on Vercel

    # Scheduler: only on local/Docker (not Vercel serverless)
    if not IS_VERCEL:
        try:
            try:
                from api.services.scheduler import start_scheduler
            except ImportError:
                from services.scheduler import start_scheduler
            start_scheduler()
            print("[BOOT] Scheduler started.")
        except Exception as e:
            print(f"[BOOT ERROR] Scheduler failed: {e}")

@app.on_event("shutdown")
def on_shutdown():
    if not IS_VERCEL:
        try:
            try:
                from api.services.scheduler import stop_scheduler
            except ImportError:
                from services.scheduler import stop_scheduler
            stop_scheduler()
        except Exception as e:
            print(f"[BOOT ERROR] Scheduler stop failed: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.index:app", host="0.0.0.0", port=8000, reload=True)
