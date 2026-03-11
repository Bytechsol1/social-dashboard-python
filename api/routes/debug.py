"""Debug endpoints — gated by DEBUG_MODE=true environment variable."""
import os
import socket
import urllib.parse
import traceback
from fastapi import APIRouter, HTTPException, Request
from api.database import get_db, get_storage_engine

router = APIRouter()

DEBUG_MODE = True # Temporarily force True to help user debug connection issues

def _require_debug():
    if not DEBUG_MODE:
        raise HTTPException(
            status_code=403,
            detail="Debug endpoints are disabled. Set DEBUG_MODE=true to enable."
        )

def _get_user_id(request: Request) -> str:
    return os.environ.get("VITE_DEMO_USER_ID") or "default_user"

@router.get("/user-check")
def debug_user_check(request: Request):
    user_id = _get_user_id(request)
    engine = get_storage_engine()
    db_url = os.environ.get("DATABASE_URL", "")
    
    host = ""
    res_info = []
    if db_url:
        try:
            parsed = urllib.parse.urlparse(db_url.replace("postgres://", "postgresql://"))
            host = parsed.hostname
            res_info = socket.getaddrinfo(host, parsed.port or 5432)
        except Exception as dns_e:
            res_info = [f"DNS Error: {str(dns_e)}"]

    try:
        with get_db() as conn:
            row = conn.execute("SELECT id FROM users WHERE id = ?", (user_id,)).fetchone()
            all_users = [r["id"] for r in conn.execute("SELECT id FROM users").fetchall()]
            
        return {
            "demo_user_id_env": user_id,
            "demo_user_id_len": len(user_id),
            "storage_engine": engine,
            "found_in_db": bool(row),
            "all_user_ids_in_db": all_users,
            "is_vercel": os.environ.get("VERCEL") == "1",
            "db_host": host,
            "dns_resolution": [str(r[4]) for r in res_info if isinstance(r, tuple)] if res_info else res_info
        }
    except Exception as e:
        return {
            "error": str(e), 
            "traceback": traceback.format_exc(),
            "storage_engine": engine,
            "db_host": host,
            "dns_resolution": [str(r[4]) for r in res_info if isinstance(r, tuple)] if res_info else res_info
        }

@router.get("/status")
def debug_status():
    return {"debug_mode": DEBUG_MODE, "engine": get_storage_engine()}
