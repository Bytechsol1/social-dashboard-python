"""Social Analytics Dashboard API routes."""
import os
import json
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel

from api.database import get_db, get_storage_engine
from api.encryption import encrypt, decrypt
from api.services.sync_engine import perform_sync

router = APIRouter()

# --- OAuth Models ---
class OAuthCode(BaseModel):
    code: str

class ManyChatKey(BaseModel):
    key: str

class InstagramToken(BaseModel):
    token: str

# --- Helpers ---
def _get_user_id(request: Request) -> str:
    # On Vercel, we use a demo ID if no auth is present, or a header
    return os.environ.get("VITE_DEMO_USER_ID") or "default_user"

# --- Routes ---

@router.get("/health")
def health_check():
    return {"status": "ok", "engine": get_storage_engine()}

@router.post("/auth/youtube/url")
async def get_youtube_auth_url(request: Request):
    from google_auth_oauthlib.flow import Flow
    
    # Robust URL detection for Vercel
    app_url = os.environ.get("APP_URL") or os.environ.get("VERCEL_URL") or "http://localhost:3000"
    if "://" not in app_url:
        app_url = f"https://{app_url}"
    app_url = app_url.rstrip("/")
    
    redirect_uri = f"{app_url}/api/auth/youtube/callback"
    
    # Ensure client config is present
    client_id = os.environ.get("GOOGLE_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        raise HTTPException(status_code=500, detail="Google OAuth credentials missing")

    client_config = {
        "web": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [redirect_uri]
        }
    }

    flow = Flow.from_client_config(
        client_config,
        scopes=[
            "https://www.googleapis.com/auth/yt-analytics.readonly",
            "https://www.googleapis.com/auth/youtube.readonly"
        ],
        redirect_uri=redirect_uri
    )
    
    auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')
    return {"url": auth_url}

@router.post("/auth/youtube/callback")
async def youtube_callback(request: Request, data: OAuthCode):
    from google_auth_oauthlib.flow import Flow
    user_id = _get_user_id(request)
    
    app_url = os.environ.get("APP_URL") or os.environ.get("VERCEL_URL") or "http://localhost:3000"
    if "://" not in app_url:
        app_url = f"https://{app_url}"
    app_url = app_url.rstrip("/")
    redirect_uri = f"{app_url}/api/auth/youtube/callback"

    client_config = {
        "web": {
            "client_id": os.environ.get("GOOGLE_CLIENT_ID"),
            "client_secret": os.environ.get("GOOGLE_CLIENT_SECRET"),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token"
        }
    }

    try:
        flow = Flow.from_client_config(client_config, scopes=[], redirect_uri=redirect_uri)
        flow.fetch_token(code=data.code)
        
        refresh_token = flow.credentials.refresh_token
        if not refresh_token:
            return JSONResponse(status_code=400, content={"error": "No refresh token received. Try re-linking with 'prompt=consent'."})

        encrypted_token = encrypt(refresh_token)
        
        with get_db() as conn:
            conn.execute(
                "INSERT INTO users (id, email, yt_refresh_token) VALUES (?, ?, ?) "
                "ON CONFLICT(id) DO UPDATE SET yt_refresh_token = excluded.yt_refresh_token",
                (user_id, "user@example.com", encrypted_token)
            )
            
        return {"success": True}
    except Exception as e:
        print(f"[AUTH ERROR] {e}")
        return JSONResponse(status_code=400, content={"error": str(e)})

@router.post("/auth/manychat")
async def connect_manychat(request: Request, data: ManyChatKey):
    user_id = _get_user_id(request)
    encrypted_key = encrypt(data.key)
    with get_db() as conn:
        conn.execute(
            "INSERT INTO users (id, email, manychat_key) VALUES (?, ?, ?) "
            "ON CONFLICT(id) DO UPDATE SET manychat_key = excluded.manychat_key",
            (user_id, "user@example.com", encrypted_key)
        )
    return {"success": True}

@router.post("/auth/instagram")
async def connect_instagram(request: Request, data: InstagramToken):
    user_id = _get_user_id(request)
    encrypted_token = encrypt(data.token)
    
    # Try to resolve IG User ID immediately
    from api.services.instagram_service import InstagramService
    ig_service = InstagramService(data.token)
    ig_user_id = await ig_service.get_user_id()
    
    with get_db() as conn:
        conn.execute(
            "INSERT INTO users (id, email, ig_access_token, ig_user_id) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(id) DO UPDATE SET ig_access_token = excluded.ig_access_token, ig_user_id = excluded.ig_user_id",
            (user_id, "user@example.com", encrypted_token, ig_user_id)
        )
    return {"success": True, "ig_user_id": ig_user_id}

@router.post("/sync")
async def trigger_sync(request: Request):
    user_id = _get_user_id(request)
    results = await perform_sync(user_id)
    return {"success": True, "result": results}

@router.get("/dashboard")
async def get_dashboard_data(request: Request):
    user_id = _get_user_id(request)
    storage = get_storage_engine()
    
    with get_db() as conn:
        # 1. Metrics (Last 30 days)
        rows = conn.execute(
            "SELECT date, source, metric_name, value, dimension FROM metrics WHERE user_id = ? ORDER BY date ASC",
            (user_id,)
        ).fetchall()
        
        # 2. Logs
        logs = [dict(r) for r in conn.execute(
            "SELECT * FROM sync_logs WHERE user_id = ? ORDER BY timestamp DESC LIMIT 20", (user_id,)
        ).fetchall()]
        
        # 3. ManyChat Automations
        automations = [dict(r) for r in conn.execute(
            "SELECT * FROM manychat_automations WHERE user_id = ? ORDER BY last_modified DESC", (user_id,)
        ).fetchall()]
        
        # 4. ManyChat Interactions
        interactions = [dict(r) for r in conn.execute(
            "SELECT * FROM manychat_interactions WHERE user_id = ? ORDER BY timestamp DESC LIMIT 20", (user_id,)
        ).fetchall()]

        # 5. YouTube Videos
        videos = [dict(r) for r in conn.execute(
            "SELECT * FROM youtube_videos WHERE user_id = ? ORDER BY published_at DESC LIMIT 10", (user_id,)
        ).fetchall()]

        # 6. Instagram Media
        ig_media = [dict(r) for r in conn.execute(
            "SELECT * FROM instagram_media WHERE user_id = ? ORDER BY timestamp DESC LIMIT 10", (user_id,)
        ).fetchall()]

    # Process metrics into chart format
    chart_map = {}
    for r in rows:
        d = r["date"]
        if d not in chart_map:
            chart_map[d] = {"date": d, "youtube_views": 0, "youtube_revenue": 0, "manychat_subscribers": 0, "instagram_followers": 0}
        
        if r["source"] == "youtube":
            if r["metric_name"] == "views": chart_map[d]["youtube_views"] = r["value"]
            if r["metric_name"] == "revenue": chart_map[d]["youtube_revenue"] = r["value"]
        elif r["source"] == "manychat":
            if r["metric_name"] == "manychat_subscribers": chart_map[d]["manychat_subscribers"] = r["value"]
        elif r["source"] == "instagram":
            if r["metric_name"] == "followers": chart_map[d]["instagram_followers"] = r["value"]

    # Recent summary
    def _latest(name, source="youtube"):
        return next((r["value"] for r in reversed(rows) if r["metric_name"] == name and r["source"] == source), 0)
        
    def _sum(name, source="youtube", days=7):
        cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        return sum(r["value"] for r in rows if r["metric_name"] == name and r["source"] == source and r["date"] >= cutoff)

    summary = {
        "youtube_subscribers":    _latest("total_subscribers"),
        "youtube_views_total":    _latest("total_views"),
        "youtube_views_recent":   _sum("views"),
        "youtube_revenue_recent": _sum("revenue"),
        "manychat_subscribers":   _latest("manychat_subscribers",     source="manychat"),
        "manychat_growth":        _latest("manychat_growth_tools",    source="manychat"),
        "ig_followers":           _latest("followers",                source="instagram"),
        "ig_media_count":         _latest("media_count",              source="instagram"),
        "ig_recent_reach":        _sum("total_reach",                 source="instagram"),
        "ig_recent_impressions":  _sum("total_impressions",           source="instagram"),
        "ig_total_likes":         _latest("total_likes",              source="instagram"),
        "ig_total_comments":      _latest("total_comments",           source="instagram"),
        "ig_total_interactions":  _latest("total_interactions",       source="instagram"),
    }

    demographics = {}

    return {
        "summary":      summary,
        "chartData":    sorted(chart_map.values(), key=lambda x: x["date"]),
        "demographics": demographics,
        "logs":         logs,
        "automations":  automations,
        "interactions": interactions,
        "videos":       videos,
        "ig_media":     ig_media,
        "storage":      storage
    }

@router.get("/status")
def get_status(request: Request):
    user_id = _get_user_id(request)
    status  = {"youtube": False, "manychat": False, "instagram": False}
    
    try:
        with get_db() as conn:
            row = conn.execute(
                "SELECT yt_refresh_token, manychat_key, ig_access_token FROM users WHERE id = ?", (user_id,)
            ).fetchone()
            if row:
                status["youtube"]   = bool(row["yt_refresh_token"])
                status["manychat"]  = bool(row["manychat_key"])
                status["instagram"] = bool(row["ig_access_token"])
    except Exception as e:
        print(f"[STATUS ERROR] {e}")
    return status
