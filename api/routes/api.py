"""API routes for the dashboard."""
import os
import json
from datetime import datetime, timezone
from typing import Optional, List, Dict
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel

from api.database import get_db, DB_PATH, get_storage_engine

router = APIRouter()

GOOGLE_CLIENT_ID     = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")

def _get_redirect_uri(request: Request) -> str:
    """Determine the redirect URI. Hardened for Vercel production."""
    # 1. Force production URL on Vercel to match Google Cloud Console EXACTLY
    if os.environ.get("VERCEL") == "1":
        return "https://social-dashboard-python.vercel.app/api/auth/youtube/callback"
    
    # 2. Local fallback
    configured_url = os.environ.get("APP_URL")
    if configured_url:
        return f"{configured_url.rstrip('/')}/api/auth/youtube/callback"
    
    # 3. Dynamic detection for dev/previews
    host = request.headers.get("x-forwarded-host") or request.headers.get("host") or "localhost:3000"
    proto = request.headers.get("x-forwarded-proto") or "http"
    return f"{proto}://{host}/api/auth/youtube/callback"

# Only 2 stable scopes — monetary scope requires extra approval and causes invalid_scope
YOUTUBE_SCOPES = [
    "https://www.googleapis.com/auth/yt-analytics.readonly",
    "https://www.googleapis.com/auth/youtube.readonly",
]


def _get_user_id(request: Request) -> str:
    """Deterministic user id — replace with session lookup in production."""
    uid = os.environ.get("VITE_DEMO_USER_ID", "134acfd2-cb6e-4356-81d9-32457fc555de")
    return uid


def _make_flow(redirect_uri: str) -> "Flow":
    """Build a Google OAuth Flow with consistent scopes + no PKCE."""
    from google_auth_oauthlib.flow import Flow
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id":     GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri":      "https://accounts.google.com/o/oauth2/auth",
                "token_uri":     "https://oauth2.googleapis.com/token",
            }
        },
        scopes=YOUTUBE_SCOPES,
    )
    flow.redirect_uri = redirect_uri
    # Disable PKCE — stateless backend cannot validate code verifier
    flow.code_verifier = None
    try:
        flow.autogenerate_code_verifier = False
    except AttributeError:
        pass
    return flow


# ── YouTube Auth ─────────────────────────────────────────────────────────────

@router.get("/auth/youtube/url")
def get_youtube_auth_url(request: Request):
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=503, detail="YouTube API credentials missing in environment variables.")
    
    redirect_uri = _get_redirect_uri(request)
    flow = _make_flow(redirect_uri)
    auth_url, _ = flow.authorization_url(prompt="consent", access_type="offline")
    # Matching the clean local JSON format
    return {"url": auth_url}


@router.get("/auth/youtube/callback")
def youtube_callback(code: str, request: Request):
    user_id = _get_user_id(request)
    redirect_uri = _get_redirect_uri(request)
    flow = _make_flow(redirect_uri)

    try:
        flow.autogenerate_code_verifier = False
    except AttributeError:
        pass

    try:
        flow.fetch_token(code=code)
        creds = flow.credentials

        from api.encryption import encrypt
        encrypted_refresh = encrypt(creds.refresh_token) if creds.refresh_token else None

        with get_db() as conn:
            # Use UPSERT: insert/update the user record. 
            # This is critical for ephemeral in-memory databases on Vercel.
            conn.execute(
                """
                INSERT INTO users (id, yt_refresh_token) VALUES (?, ?)
                ON CONFLICT(id) DO UPDATE SET yt_refresh_token = excluded.yt_refresh_token
                """,
                (user_id, encrypted_refresh),
            )

        return HTMLResponse(content="""
            <html><body>
              <script>
                if (window.opener) {
                  window.opener.postMessage({ type: 'YOUTUBE_CONNECTED' }, '*');
                  window.close();
                }
              </script>
              <p>✅ YouTube connected! You can close this window.</p>
            </body></html>
        """)
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(f"[AUTH] YouTube callback error: {e}\n{tb}")
        # Removed file logging due to Vercel read-only filesystem
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")


# ── ManyChat Auth ─────────────────────────────────────────────────────────────

class ManyChatKey(BaseModel):
    key: str


@router.post("/auth/manychat")
def connect_manychat(request: Request, data: ManyChatKey):
    from api.encryption import encrypt
    user_id = _get_user_id(request)
    encrypted_key = encrypt(data.key)
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO users (id, manychat_key) VALUES (?, ?)
            ON CONFLICT(id) DO UPDATE SET manychat_key = excluded.manychat_key
            """,
            (user_id, encrypted_key),
        )
    return {"success": True}


# ── Instagram Auth ────────────────────────────────────────────────────────────

class InstagramToken(BaseModel):
    token: str


@router.post("/auth/instagram")
def connect_instagram(request: Request, data: InstagramToken):
    print(f"[AUTH] Instagram connect request received for user: {_get_user_id(request)}")
    from api.encryption import encrypt
    user_id = _get_user_id(request)
    encrypted_token = encrypt(data.token)
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO users (id, ig_access_token) VALUES (?, ?)
            ON CONFLICT(id) DO UPDATE SET ig_access_token = excluded.ig_access_token
            """,
            (user_id, encrypted_token),
        )
    return {"success": True}


# ── Sync Routes ─────────────────────────────────────────────────────────────

@router.post("/sync")
async def trigger_sync(request: Request):
    from api.services.sync_engine import perform_sync
    user_id = _get_user_id(request)
    try:
        result = await perform_sync(user_id)
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sync/manychat")
async def sync_manychat_route(request: Request):
    from api.services.sync_engine import perform_sync
    user_id = _get_user_id(request)
    try:
        await perform_sync(user_id)
        with get_db() as conn:
            rows = conn.execute(
                "SELECT * FROM manychat_automations WHERE user_id = ?", (user_id,)
            ).fetchall()
        return {"success": True, "automations": [dict(r) for r in rows]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


# ── Trends / AI Inspiration ───────────────────────────────────────────────────

@router.post("/trends/inspiration")
@router.post("/trends/inspiration/{user_id}")
async def trends_inspiration(request: Request, user_id: Optional[str] = None):
    if not user_id:
        user_id = _get_user_id(request)
    """Generate AI content ideas using top videos + ManyChat flow names via Claude."""
    import httpx as _httpx

    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not anthropic_key:
        raise HTTPException(status_code=503, detail="ANTHROPIC_API_KEY not configured")

    with get_db() as conn:
        top_videos = [dict(r) for r in conn.execute(
            "SELECT title, view_count, like_count FROM youtube_videos "
            "WHERE user_id = ? ORDER BY view_count DESC LIMIT 5",
            (user_id,)
        ).fetchall()]
        flow_names = [r["name"] for r in conn.execute(
            "SELECT name FROM manychat_automations WHERE user_id = ? LIMIT 10",
            (user_id,)
        ).fetchall()]

    if not top_videos and not flow_names:
        # No data yet — return placeholder ideas
        return {
            "ideas": [],
            "note": "No video or automation data found. Run a sync first.",
        }

    videos_ctx = json.dumps(top_videos)
    flows_ctx  = json.dumps(flow_names)

    prompt = f"""You are a YouTube growth strategist. Analyze these top-performing videos:
{videos_ctx}

And these active audience automation flows:
{flows_ctx}

Generate exactly 5 specific, actionable content ideas that would resonate with this creator's audience.
Return ONLY a valid JSON array with this exact schema (no markdown, no extra text):
[{{"title": "...", "hook": "...", "estimated_ctr": "X.X%"}}]"""

    try:
        async with _httpx.AsyncClient(timeout=30) as client:
            res = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key":         anthropic_key,
                    "anthropic-version": "2023-06-01",
                    "content-type":      "application/json",
                },
                json={
                    "model":      "claude-3-haiku-20240307",
                    "max_tokens": 1024,
                    "messages":   [{"role": "user", "content": prompt}],
                },
            )
        resp_json = res.json()
        raw_text  = resp_json["content"][0]["text"].strip()
        # Strip markdown code fences if present
        if raw_text.startswith("```"):
            raw_text = raw_text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        ideas = json.loads(raw_text)
        return {"ideas": ideas, "source": "claude"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI generation failed: {str(e)}")


# ── Dashboard Data ────────────────────────────────────────────────────────────

@router.get("/track/manychat/{user_id}/{automation_id}/{event_type}")
async def track_manychat(user_id: str, automation_id: str, event_type: str):
    """Endpoint for ManyChat External Request to track runs and clicks.
    event_type: 'run' or 'click'
    """
    with get_db() as conn:
        # 1. Record the ping
        conn.execute(
            "INSERT INTO manychat_pings (user_id, automation_id, type) VALUES (?, ?, ?)",
            (user_id, automation_id, event_type)
        )
        
        # 2. Update the automation record (ensure record exists first)
        # We try to find existing flow or create placeholder
        row = conn.execute(
            "SELECT id FROM manychat_automations WHERE id = ?", (automation_id,)
        ).fetchone()
        
        if not row:
            # Create placeholder if it doesn't exist yet (sync hasn't run)
            conn.execute(
                "INSERT INTO manychat_automations (id, user_id, name, runs, clicks, ctr) VALUES (?, ?, ?, 0, 0, 0)",
                (automation_id, user_id, f"Flow {automation_id}")
            )
            
        if event_type == "run":
            conn.execute(
                "UPDATE manychat_automations SET runs = runs + 1 WHERE id = ?",
                (automation_id,)
            )
        elif event_type == "click":
            conn.execute(
                "UPDATE manychat_automations SET clicks = clicks + 1 WHERE id = ?",
                (automation_id,)
            )
            
        # 3. Recalculate CTR
        conn.execute("""
            UPDATE manychat_automations 
            SET ctr = CASE WHEN runs > 0 THEN (CAST(clicks AS REAL) / runs) * 100 ELSE 0 END
            WHERE id = ?
        """, (automation_id,))
        
    return {"status": "success", "event": event_type}


@router.get("/dashboard")
@router.get("/dashboard/{user_id}")
async def get_dashboard(request: Request, user_id: Optional[str] = None):
    if not user_id:
        user_id = _get_user_id(request)

    # 1. Resilience: Report storage type
    from api.database import get_storage_engine
    storage = get_storage_engine()
    
    if storage == "sqlite_memory":
        return {
            "summary": {"total_views": 0, "total_subscribers": 0, "active_automations": 0, "avg_ctr": 0},
            "chartData": [], "automations": [], "videos": [],
            "status": "Healthy (Internal Memory Only)",
            "storage": storage
        }

    try:
        with get_db() as conn:
            metrics = [dict(r) for r in conn.execute(
                "SELECT * FROM metrics WHERE user_id = ? ORDER BY date ASC",
                (user_id,)
            ).fetchall()]
            logs = [dict(r) for r in conn.execute(
                "SELECT * FROM sync_logs WHERE user_id = ? ORDER BY timestamp DESC LIMIT 10",
                (user_id,)
            ).fetchall()]
            videos = [dict(r) for r in conn.execute(
                "SELECT * FROM youtube_videos WHERE user_id = ? ORDER BY published_at DESC LIMIT 10",
                (user_id,)
            ).fetchall()]
            automations = [dict(r) for r in conn.execute(
                "SELECT * FROM manychat_automations WHERE user_id = ? ORDER BY last_modified DESC, name ASC",
                (user_id,)
            ).fetchall()]
            interactions = [dict(r) for r in conn.execute(
                "SELECT * FROM manychat_interactions WHERE user_id = ? ORDER BY timestamp DESC LIMIT 20",
                (user_id,)
            ).fetchall()]
            ig_media = [dict(r) for r in conn.execute(
                "SELECT * FROM instagram_media WHERE user_id = ? ORDER BY timestamp DESC LIMIT 20",
                (user_id,)
            ).fetchall()]
            user_row = conn.execute(
                "SELECT ig_audience_json FROM users WHERE id = ?", (user_id,)
            ).fetchone()
            ig_audience = json.loads(user_row["ig_audience_json"]) if user_row and user_row["ig_audience_json"] else None

    except Exception as e:
        print(f"[ERROR] get_dashboard DB failure: {e}")
        return {
            "summary": {}, "chartData": [], "automations": [], "videos": [], "status": "error",
            "demographics": {"ageGender": {}, "countries": [], "subscriberTrend": [], "instagram": {"cities": [], "countries": [], "ageGender": {}}},
            "logs": [], "interactions": [], "ig_media": [], "storage": storage
        }

    # ── Build time-series chart data (daily YouTube + Instagram metrics)
    chart_map: dict = {}
    for m in metrics:
        if m["source"] == "youtube" and m.get("dimension", "none") == "none":
             d = m["date"]
             if d not in chart_map: chart_map[d] = {"date": d}
             chart_map[d][f"youtube_{m['metric_name']}"] = m["value"]
        elif m["source"] == "instagram" and m.get("dimension", "none") == "none":
             d = m["date"]
             if d not in chart_map: chart_map[d] = {"date": d}
             chart_map[d][f"instagram_{m['metric_name']}"] = m["value"]

    # ── Demographics
    age_gender_data: dict = {}
    country_data: list    = []
    subscriber_trend: list = []

    # Instagram Demographics (Priority)
    ig_demographics = {"cities": [], "countries": [], "ageGender": {}}
    if ig_audience:
        for item in ig_audience:
            name = item["name"]
            values = item["values"][0]["value"]
            if name == "audience_city":
                ig_demographics["cities"] = sorted([{"city": k, "value": v} for k, v in values.items()], key=lambda x: x["value"], reverse=True)[:10]
            elif name == "audience_country":
                ig_demographics["countries"] = sorted([{"country": k, "views": v} for k, v in values.items()], key=lambda x: x["views"], reverse=True)[:10]
            elif name == "audience_gender_age":
                ig_demographics["ageGender"] = values

    # YouTube Demographics (Legacy)
    demo_rows = [m for m in metrics if m["source"] == "youtube_demo"]
    for m in demo_rows:
        if m["metric_name"] == "viewerPercentage":
            dim = m.get("dimension", "")
            age_gender_data[dim] = m["value"]
        elif m["metric_name"] in ("subscribersGained", "subscribersLost"):
            d = m["date"]
            if d not in chart_map: chart_map[d] = {"date": d} # fallback
            # We add to subscriber_trend later

    # Country views
    country_map: dict = {}
    for m in demo_rows:
        if m["metric_name"] == "countryViews":
            country = m.get("dimension", "")
            if country not in country_map or m["date"] > country_map[country]["date"]:
                country_map[country] = {"country": country, "views": m["value"], "date": m["date"]}
    country_data = sorted(country_map.values(), key=lambda x: x["views"], reverse=True)[:10]

    sub_map: dict = {}
    for m in demo_rows:
        if m["metric_name"] in ("subscribersGained", "subscribersLost"):
            d = m["date"]
            if d not in sub_map: sub_map[d] = {"date": d}
            sub_map[d][m["metric_name"]] = m["value"]
    subscriber_trend = sorted(sub_map.values(), key=lambda x: x["date"])[-30:]

    demographics = {
        "ageGender":       age_gender_data,
        "countries":       country_data,
        "subscriberTrend": subscriber_trend,
        "instagram":       ig_demographics
    }

    # ── Helpers for summary
    def _latest(name: str, source: str = "youtube") -> Optional[float]:
        matches = [
            m for m in metrics
            if m["metric_name"] == name and m["source"] == source
               and m.get("dimension", "none") == "none"
        ]
        if not matches: return None
        return float(sorted(matches, key=lambda x: x["date"], reverse=True)[0]["value"])

    def _sum(name: str, source: str = "youtube") -> Optional[float]:
        vals = [
            m["value"] for m in metrics
            if m["metric_name"] == name and m["source"] == source
               and m.get("dimension", "none") == "none"
        ]
        if not vals: return 0.0
        return float(sum(vals))

    summary = {
        "recent_views":           _sum("views"),
        "total_views":            _latest("total_views"),
        "total_videos":           _latest("total_videos"),
        "recent_likes":           _sum("likes"),
        "recent_comments":        _sum("comments"),
        "revenue":                _sum("revenue"),
        "subscribers":            _latest("total_subscribers"),
        "watch_time_minutes":     _sum("watch_time_minutes"),
        # ManyChat 
        "manychat_subscribers":   _latest("manychat_subscribers",     source="manychat"),
        "active_widgets":         _latest("manychat_active_widgets",  source="manychat"),
        "total_flows":            _latest("manychat_total_flows",     source="manychat"),
        # Instagram
        "ig_followers":           _latest("followers",                source="instagram"),
        "ig_media_count":         _latest("media_count",              source="instagram"),
        "ig_recent_reach":        _sum("total_reach",                 source="instagram"),
        "ig_recent_impressions":  _sum("total_impressions",           source="instagram"),
        "ig_total_likes":         _latest("total_likes",              source="instagram"),
        "ig_total_comments":      _latest("total_comments",           source="instagram"),
        "ig_total_interactions":  _latest("total_interactions",       source="instagram"),
    }

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

@router.get("/debug/user-check")
def debug_user_check(request: Request):
    user_id = _get_user_id(request)
    engine = get_storage_engine()
    
    try:
        with get_db() as conn:
            # Check for exact match
            row = conn.execute("SELECT id FROM public.users WHERE id = ?", (user_id,)).fetchone()
            # List all users for debugging
            all_users = [r["id"] for r in conn.execute("SELECT id FROM public.users").fetchall()]
            
        return {
            "demo_user_id_env": user_id,
            "demo_user_id_len": len(user_id),
            "storage_engine": engine,
            "found_in_db": bool(row),
            "all_user_ids_in_db": all_users,
            "id_match_check": user_id in all_users if all_users else False,
            "is_vercel": os.environ.get("VERCEL") == "1"
        }
    except Exception as e:
        return {"error": str(e), "storage_engine": engine}
