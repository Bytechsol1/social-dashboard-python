"""Social Analytics Dashboard API routes."""
import os
import json
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from urllib.parse import urlencode, quote

from fastapi import APIRouter, Request, HTTPException, Depends, File, UploadFile, Form
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse
from pydantic import BaseModel

from api.database import get_db, get_storage_engine
from api.encryption import encrypt, decrypt
from api.services.sync_engine import perform_sync
from api.services.gemini_service import GeminiService
from api.services.storage_service import StorageService
from api.services.instagram_service import InstagramService

router = APIRouter()

# --- OAuth Models ---
class OAuthCode(BaseModel):
    code: str

class ManyChatKey(BaseModel):
    key: str

class InstagramToken(BaseModel):
    token: str

class SchedulePost(BaseModel):
    caption: str
    scheduled_at: str # ISO string
    is_queued: bool = False

class PostNowRequest(BaseModel):
    caption: str

# --- Helpers ---
def _get_user_id(request: Request) -> str:
    # On Vercel, we use a demo ID if no auth is present, or a header
    return os.environ.get("VITE_DEMO_USER_ID") or "default_user"

# --- Routes ---

@router.get("/auth/youtube/url")
async def get_youtube_auth_url(request: Request):
    from google_auth_oauthlib.flow import Flow
    print("[AUTH] Generating YouTube connection URL...")
    
    try:
        # Robust URL detection for Vercel
        app_url = os.environ.get("APP_URL") or os.environ.get("VERCEL_URL") or "http://localhost:3000"
        if "://" not in app_url:
            app_url = f"https://{app_url}"
        app_url = app_url.rstrip("/")
        
        redirect_uri = f"{app_url}/api/auth/youtube/callback"
        print(f"[AUTH] Using redirect_uri: {redirect_uri}")
        
        # Ensure client config is present
        client_id = os.environ.get("GOOGLE_CLIENT_ID")
        client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
        
        if not client_id or not client_secret:
            print("[AUTH ERROR] Missing credentials in environment")
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

        from urllib.parse import urlencode
        
        scopes = [
            "https://www.googleapis.com/auth/yt-analytics.readonly",
            "https://www.googleapis.com/auth/youtube.readonly",
            "https://www.googleapis.com/auth/youtube.force-ssl"
        ]
        
        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(scopes),
            "access_type": "offline",
            "prompt": "consent",
            "include_granted_scopes": "true"
        }
        
        auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
        print(f"[AUTH] Successfully generated manual URL: {auth_url[:50]}...")
        return {"url": auth_url}
    except Exception as e:
        import traceback
        print(f"[AUTH FATAL ERROR] {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/auth/youtube/callback")
async def youtube_callback(request: Request, code: str):
    """Handle Google OAuth callback using direct HTTP token exchange (no PKCE needed)."""
    import httpx
    user_id = _get_user_id(request)
    print(f"[AUTH] Callback received for user {user_id}")
    
    app_url = os.environ.get("APP_URL") or os.environ.get("VERCEL_URL") or "http://localhost:3000"
    if "://" not in app_url:
        app_url = f"https://{app_url}"
    app_url = app_url.rstrip("/")
    redirect_uri = f"{app_url}/api/auth/youtube/callback"

    client_id = os.environ.get("GOOGLE_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")

    try:
        # Direct HTTP token exchange — bypasses PKCE requirement
        # that breaks on Vercel serverless (code_verifier is lost between invocations)
        async with httpx.AsyncClient() as client:
            token_resp = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                },
            )
        
        token_data = token_resp.json()
        print(f"[AUTH] Token response keys: {list(token_data.keys())}")
        
        if "error" in token_data:
            raise Exception(f"({token_data['error']}) {token_data.get('error_description', 'Unknown error')}")
        
        refresh_token = token_data.get("refresh_token")
        if not refresh_token:
            print("[AUTH WARNING] No refresh token received")

        encrypted_token = encrypt(refresh_token) if refresh_token else None
        
        with get_db() as conn:
            if encrypted_token:
                conn.execute(
                    "INSERT INTO users (id, email, yt_refresh_token) VALUES (?, ?, ?) "
                    "ON CONFLICT(id) DO UPDATE SET yt_refresh_token = excluded.yt_refresh_token",
                    (user_id, "user@example.com", encrypted_token)
                )
            else:
                print("[AUTH] Skipping DB update (no new refresh token)")
            
        return HTMLResponse(content="""
            <html>
                <body style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:100vh;font-family:sans-serif;background:#0B0E14;color:white;">
                    <h1 style="color:#FF0000;">✅ YouTube Connected!</h1>
                    <p>This window will close automatically.</p>
                    <script>
                        if (window.opener) {
                            window.opener.postMessage({type: 'OAUTH_SUCCESS'}, '*');
                        }
                        setTimeout(() => window.close(), 1500);
                    </script>
                </body>
            </html>
        """)
    except Exception as e:
        import traceback
        error_msg = str(e)
        print(f"[AUTH ERROR] {error_msg}")
        print(traceback.format_exc())
        return HTMLResponse(content=f"""
            <html>
                <body style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:100vh;font-family:sans-serif;background:#0B0E14;color:white;padding:20px;text-align:center;">
                    <h1 style="color:#f43f5e;">Connection Failed</h1>
                    <p>{error_msg}</p>
                    <button onclick="window.close()" style="margin-top:20px;padding:10px 20px;background:#f43f5e;color:white;border:none;border-radius:8px;cursor:pointer;">Close Window</button>
                </body>
            </html>
        """)

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

class YoutubeReplyRequest(BaseModel):
    parentId: str
    text: str

@router.get("/youtube/comments")
async def get_youtube_comments(request: Request):
    from api.services.youtube_comments import fetch_comments
    user_id = _get_user_id(request)
    try:
        comments = await fetch_comments(user_id)
        return {"success": True, "comments": comments}
    except Exception as e:
        import traceback
        print(f"[YOUTUBE COMMENTS ERROR]")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/youtube/comments/reply")
async def post_youtube_reply(request: Request, data: YoutubeReplyRequest):
    from api.services.youtube_comments import post_reply
    user_id = _get_user_id(request)
    try:
        res = await post_reply(user_id, data.parentId, data.text)
        return {"success": True, "reply": res}
    except Exception as e:
        print(f"[YOUTUBE REPLY ERROR] {e}")
        raise HTTPException(status_code=500, detail=str(e))

class DeleteCommentRequest(BaseModel):
    commentId: str

@router.post("/youtube/comments/delete")
async def post_delete_comment(request: Request, data: DeleteCommentRequest):
    from api.services.youtube_comments import delete_comment
    user_id = _get_user_id(request)
    try:
        await delete_comment(user_id, data.commentId)
        return {"success": True}
    except Exception as e:
        print(f"[YOUTUBE DELETE ERROR] {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sync")
async def trigger_sync(request: Request):
    user_id = _get_user_id(request)
    results = await perform_sync(user_id)
    return {"success": True, "result": results}

@router.get("/dashboard")
async def get_dashboard_data(request: Request):
    user_id = _get_user_id(request)
    days = int(request.query_params.get("days", "30"))
    start_date = request.query_params.get("start_date")
    end_date = request.query_params.get("end_date")
    
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
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d") if not (start_date and end_date) else None
        for r in rows:
            d = r["date"]
            if start_date and end_date:
                if d < start_date or d > end_date:
                    continue
            elif cutoff_date and d < cutoff_date:
                continue
            if d not in chart_map:
                chart_map[d] = {
                    "date": d, 
                    "youtube_views": 0, 
                    "youtube_revenue": 0, 
                    "manychat_subscribers": 0, 
                    "instagram_followers": 0,
                    "instagram_reach": 0
                }
            
            if r["source"] == "youtube":
                if r["metric_name"] == "views": chart_map[d]["youtube_views"] = r["value"]
                if r["metric_name"] == "revenue": chart_map[d]["youtube_revenue"] = r["value"]
            elif r["source"] == "manychat":
                if r["metric_name"] == "manychat_subscribers": chart_map[d]["manychat_subscribers"] = r["value"]
            elif r["source"] == "instagram":
                if r["metric_name"] == "followers": chart_map[d]["instagram_followers"] = r["value"]
                if r["metric_name"] == "total_reach": chart_map[d]["instagram_reach"] = r["value"]

        # Recent summary
        def _latest(name, source="youtube"):
            return next((r["value"] for r in reversed(rows) if r["metric_name"] == name and r["source"] == source), 0)
            
        def _sum(name, source="youtube", custom_days=None):
            if start_date and end_date and custom_days is None:
                return sum(r["value"] for r in rows if r["metric_name"] == name and r["source"] == source and start_date <= r["date"] <= end_date)
            target_days = custom_days if custom_days is not None else days
            cutoff = (datetime.now() - timedelta(days=target_days)).strftime("%Y-%m-%d")
            return sum(r["value"] for r in rows if r["metric_name"] == name and r["source"] == source and r["date"] >= cutoff)

        # Calculate individual platform reach for the selected period
        yt_reach = _sum("views", source="youtube")
        ig_reach = _sum("total_reach", source="instagram")
        mc_reach = _sum("manychat_active_widgets", source="manychat")

        summary = {
            # YouTube Specific
            "youtube_subscribers":    _latest("total_subscribers"),
            "youtube_views_total":    _latest("total_views"),
            "youtube_views_recent":   yt_reach,
            "youtube_revenue_recent": _sum("revenue"),
            "youtube_reach":          yt_reach,
            
            # General/Legacy Keys (REQUIRED BY FRONTEND)
            "subscribers":            _latest("total_subscribers"),
            "total_views":            _latest("total_views"),
            "revenue":                _sum("revenue"),
            "watch_time_minutes":     _sum("watch_time_minutes"),
            "avg_duration":           _latest("avg_view_duration"),
            "total_videos":           _latest("total_videos"),
            "subs_gained":            _sum("subs_gained"),
            "subs_lost":              _sum("subs_lost"),

            # ManyChat
            "manychat_subscribers":   _latest("manychat_subscribers",     source="manychat"),
            "manychat_growth":        _latest("manychat_growth_tools",    source="manychat"),
            "total_flows":            _latest("manychat_total_flows",     source="manychat"),
            "manychat_reach":         mc_reach,

            # Instagram
            "ig_followers":           _latest("followers",                source="instagram"),
            "ig_media_count":         _latest("media_count",              source="instagram"),
            "ig_recent_reach":        ig_reach,
            "ig_recent_impressions":  _sum("total_impressions",           source="instagram"),
            "ig_total_likes":         _latest("total_likes",              source="instagram"),
            "ig_total_comments":      _latest("total_comments",           source="instagram"),
            "ig_total_interactions":  _latest("total_interactions",       source="instagram"),
            "instagram_reach":        ig_reach,

            # Feature: Combined Reach
            "combined_reach":         yt_reach + ig_reach + mc_reach
        }

        # Process demographics
        age_gender = {}
        countries = []
        subscriber_trend = []
        
        # Get latest demographics
        demo_rows = [dict(r) for r in conn.execute(
            "SELECT metric_name, value, dimension FROM metrics WHERE user_id = ? AND source = 'youtube_demo' "
            "AND date = (SELECT MAX(date) FROM metrics WHERE user_id = ? AND source = 'youtube_demo')",
            (user_id, user_id)
        ).fetchall()]
        
        for dr in demo_rows:
            if dr["metric_name"] == "viewerPercentage":
                age_gender[dr["dimension"]] = dr["value"]
            elif dr["metric_name"] == "countryViews":
                countries.append({"country": dr["dimension"], "views": int(dr["value"])})
        
        # Sort countries by views
        countries = sorted(countries, key=lambda x: x["views"], reverse=True)
        
        # Subscriber trend (last 30 days)
        trend_data = {}
        for r in rows:
            if r["source"] == "youtube" and r["metric_name"] in ["subs_gained", "subs_lost"]:
                d = r["date"]
                if d not in trend_data: trend_data[d] = {"date": d, "subscribersGained": 0, "subscribersLost": 0}
                if r["metric_name"] == "subs_gained": trend_data[d]["subscribersGained"] = r["value"]
                if r["metric_name"] == "subs_lost": trend_data[d]["subscribersLost"] = r["value"]
        
        subscriber_trend = sorted(trend_data.values(), key=lambda x: x["date"])

        # Instagram audience
        ig_audience_formatted = {"ageGender": {}}
        user_row = conn.execute("SELECT ig_audience_json FROM users WHERE id = ?", (user_id,)).fetchone()
        if user_row and user_row["ig_audience_json"]:
            try:
                raw_ig = json.loads(user_row["ig_audience_json"])
                # raw_ig is a list of metrics
                for metric in raw_ig:
                    if metric.get("name") in ["follower_demographics", "reached_audience_demographics"]:
                        # Extract age/gender from values[0][value]
                        vals = metric.get("values", [])
                        if vals and "value" in vals[0]:
                            # This is usually a dict like {"F.18-24": 123, ...}
                            ig_audience_formatted["ageGender"].update(vals[0]["value"])
            except: pass

        demographics = {
            "ageGender": age_gender,
            "countries": countries,
            "subscriberTrend": subscriber_trend,
            "instagram": ig_audience_formatted
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

@router.get("/youtube/ideas")
async def get_youtube_ideas(request: Request):
    user_id = _get_user_id(request)
    
    with get_db() as conn:
        ideas = [dict(r) for r in conn.execute(
            "SELECT * FROM youtube_ideas WHERE user_id = ? ORDER BY created_at DESC LIMIT 10", (user_id,)
        ).fetchall()]
    
    if not ideas:
        # Generate new ideas if none exist
        gemini = GeminiService()
        new_ideas = await gemini.generate_video_ideas()
        
        with get_db() as conn:
            for idea in new_ideas:
                conn.execute(
                    "INSERT INTO youtube_ideas (user_id, title, description, suggested_month_year) VALUES (?, ?, ?, ?)",
                    (user_id, idea["title"], idea["description"], idea["suggested_month_year"])
                )
            ideas = [dict(r) for r in conn.execute(
                "SELECT * FROM youtube_ideas WHERE user_id = ? ORDER BY created_at DESC LIMIT 10", (user_id,)
            ).fetchall()]
            
    return {"ideas": ideas}

@router.get("/youtube/shorts-suggestions")
async def get_shorts_suggestions(request: Request, video_id: str, force: bool = False):
    user_id = _get_user_id(request)
    
    with get_db() as conn:
        if force:
            conn.execute("DELETE FROM youtube_shorts_suggestions WHERE user_id = ? AND video_id = ?", (user_id, video_id))
            suggestions = []
        else:
            suggestions = [dict(r) for r in conn.execute(
                "SELECT * FROM youtube_shorts_suggestions WHERE user_id = ? AND video_id = ?", (user_id, video_id)
            ).fetchall()]
        
        if not suggestions:
            video = conn.execute("SELECT title, description, id FROM youtube_videos WHERE id = ?", (video_id,)).fetchone()
            if video:
                video_title = video["title"] or ""
                video_desc = video["description"] or ""
                try:
                    gemini = GeminiService()
                    new_suggs = await gemini.suggest_shorts_timestamps(video_title, video_desc)
                    for s in new_suggs:
                        conn.execute(
                            "INSERT INTO youtube_shorts_suggestions (user_id, video_id, start_time, stop_time, reason) VALUES (?, ?, ?, ?, ?)",
                            (user_id, video_id, s["start_time"], s["stop_time"], s["reason"])
                        )
                except Exception as e:
                    print(f"[get_shorts_suggestions] Gemini suggesting failed: {e}")
                suggestions = [dict(r) for r in conn.execute(
                    "SELECT * FROM youtube_shorts_suggestions WHERE user_id = ? AND video_id = ?", (user_id, video_id)
                ).fetchall()]
        
        # Enrich with video title
        video_row = conn.execute("SELECT title FROM youtube_videos WHERE id = ?", (video_id,)).fetchone()
        video_title = video_row["title"] if video_row else video_id
        for s in suggestions:
            s["video_title"] = video_title
            s["recommendation_basis"] = "Video title, description & engagement pattern analysis"
                
    return {"suggestions": suggestions}

class StrategyRequest(BaseModel):
    video_id: str

@router.post("/ai/strategy")
async def generate_ai_strategy(request: Request, body: StrategyRequest):
    user_id = _get_user_id(request)
    
    with get_db() as conn:
        video = conn.execute("SELECT title, description FROM youtube_videos WHERE id = ? AND user_id = ?", (body.video_id, user_id)).fetchone()
        
        ig_media = [dict(r) for r in conn.execute(
            "SELECT caption, like_count, comments_count, media_type, timestamp FROM instagram_media WHERE user_id = ? ORDER BY timestamp DESC LIMIT 50", (user_id,)
        ).fetchall()]
    
    title = video["title"] if video else "Unknown Video"
    desc = video["description"] if video else "No description"
    ig_context = json.dumps([{k: v for k, v in m.items() if v} for m in ig_media][:10]) # Send a sample to avoid token limit overflow

    gemini = GeminiService()
    strategy_markdown = await gemini.generate_viral_strategy(title, desc, ig_context)
    return {"markdown": strategy_markdown}

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

@router.post("/settings/instagram")
async def update_instagram_settings(request: Request, body: Dict[str, Any]):
    user_id = _get_user_id(request)
    post_time = body.get("daily_post_time")
    with get_db() as conn:
        conn.execute("UPDATE users SET ig_daily_post_time = ? WHERE id = ?", (post_time, user_id))
    return {"success": True}

@router.post("/instagram/schedule")
async def schedule_instagram_post(
    request: Request,
    file: Optional[UploadFile] = File(None),
    caption: str = Form(""),
    scheduled_at: str = Form(""),
    is_queued: str = Form("false")
):
    user_id = _get_user_id(request)
    is_queued_bool = is_queued == "true"
    
    # Check if Instagram is linked and resolve ID if missing
    with get_db() as conn:
        user_row = conn.execute(
            "SELECT ig_access_token, ig_user_id FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        
        if not user_row or not user_row["ig_access_token"]:
            raise HTTPException(status_code=400, detail="Instagram not connected. Please check your token in .env")
        
        ig_user_id = user_row["ig_user_id"]
        if not ig_user_id:
            print("[DEBUG] IG User ID missing for schedule, attempting to resolve...")
            token = decrypt(user_row["ig_access_token"])
            ig_service = InstagramService(token)
            ig_user_id = await ig_service.get_user_id()
            if not ig_user_id:
                raise HTTPException(status_code=400, detail="Could not resolve Instagram Business ID. Your token might be blocked or invalid.")
            # Save it
            conn.execute("UPDATE users SET ig_user_id = ? WHERE id = ?", (ig_user_id, user_id))
    
    print(f"[DEBUG] Schedule request: caption={caption}, scheduled_at={scheduled_at}, is_queued={is_queued}")
    if not file:
        print("[DEBUG] No file received in request")
        raise HTTPException(status_code=400, detail="DEBUG: No file found in request")

    try:
        # 1. Detect media type
        media_type = "IMAGE"
        if file.content_type and "video" in file.content_type:
            media_type = "VIDEO"
        
        print(f"[DEBUG] Processing {media_type}: {file.filename}")

        # 2. Upload to Supabase Storage
        storage = StorageService()
        content = await file.read()
        media_url = await storage.upload_file(content, file.filename, file.content_type)
        
        # 3. Handle Queue Logic
        if is_queued_bool:
            with get_db() as conn:
                user_row = conn.execute("SELECT ig_daily_post_time FROM users WHERE id = ?", (user_id,)).fetchone()
                daily_time = user_row["ig_daily_post_time"] if user_row and user_row.get("ig_daily_post_time") else "18:00"
                
                # Find the last scheduled post in the queue
                last_post = conn.execute(
                    "SELECT scheduled_at FROM instagram_posts WHERE user_id = ? AND status = 'pending' ORDER BY scheduled_at DESC LIMIT 1",
                    (user_id,)
                ).fetchone()
                
                now = datetime.now(timezone.utc)
                hour, minute = map(int, daily_time.split(":"))
                
                if last_post:
                    try:
                        last_time = datetime.strptime(last_post["scheduled_at"], "%Y-%m-%d %H:%M:%S")
                        scheduled_at_dt = last_time + timedelta(days=1)
                    except Exception:
                        scheduled_at_dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0) + timedelta(days=1)
                else:
                    scheduled_at_dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    if scheduled_at_dt <= now:
                        scheduled_at_dt += timedelta(days=1)
                
                scheduled_at = scheduled_at_dt.strftime("%Y-%m-%d %H:%M:%S")

        # 4. Save to DB
        with get_db() as conn:
            conn.execute(
                "INSERT INTO instagram_posts (user_id, media_url, caption, scheduled_at, media_type, is_queued, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (user_id, media_url, caption, scheduled_at, media_type, is_queued_bool, "pending")
            )
        
        return {"success": True, "media_url": media_url, "scheduled_at": scheduled_at}
    except Exception as e:
        print(f"[ERROR] Scheduling failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/instagram/publish-now")
async def publish_instagram_now(
    request: Request,
    file: UploadFile = File(...),
    caption: str = Form("")
):
    user_id = _get_user_id(request)

    # 1. Detect media type
    media_type = "IMAGE"
    if file.content_type and "video" in file.content_type:
        media_type = "VIDEO"

    # 2. Upload to Supabase Storage
    storage = StorageService()
    content = await file.read()
    media_url = await storage.upload_file(content, file.filename, file.content_type)

    # 3. Get user token
    with get_db() as conn:
        user_row = conn.execute(
            "SELECT ig_access_token, ig_user_id FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        
        if not user_row or not user_row["ig_access_token"]:
            raise HTTPException(status_code=400, detail="Instagram not connected. Please check your token in .env")
        
        token = decrypt(user_row["ig_access_token"])
        ig_user_id = user_row["ig_user_id"]

        # 3.5 Auto-resolve IG User ID if missing
        if not ig_user_id:
            print("[DEBUG] IG User ID missing in DB, attempting to resolve...")
            ig_service = InstagramService(token)
            ig_user_id = await ig_service.get_user_id()
            if not ig_user_id:
                raise HTTPException(status_code=400, detail="Could not resolve Instagram Business ID. Your token might be blocked or invalid.")
            # Save it for next time
            with get_db() as update_conn:
                update_conn.execute("UPDATE users SET ig_user_id = ? WHERE id = ?", (ig_user_id, user_id))
        
        # 4. Publish
        ig_service = InstagramService(token)
        ig_media_id = await ig_service.post_media(ig_user_id, media_url, caption, media_type)
        
        # 5. Save to history
        conn.execute(
            "INSERT INTO instagram_posts (user_id, media_url, caption, media_type, status, ig_media_id, scheduled_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, media_url, caption, media_type, "published", ig_media_id, datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"))
        )

    return {"success": True, "ig_media_id": ig_media_id}

@router.get("/instagram/scheduled-posts")
async def get_scheduled_posts(request: Request):
    user_id = _get_user_id(request)
    with get_db() as conn:
        posts = [dict(r) for r in conn.execute(
            "SELECT * FROM instagram_posts WHERE user_id = ? ORDER BY created_at DESC", (user_id,)
        ).fetchall()]
    return {"posts": posts}

@router.delete("/instagram/scheduled-posts/{post_id}")
async def cancel_scheduled_post(request: Request, post_id: int):
    user_id = _get_user_id(request)
    with get_db() as conn:
        conn.execute(
            "DELETE FROM instagram_posts WHERE id = ? AND user_id = ? AND status = 'pending'",
            (post_id, user_id)
        )
    return {"success": True}
