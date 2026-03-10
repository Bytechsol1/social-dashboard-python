"""Sync engine — YouTube + ManyChat data sync with full diagnostics."""
import os
import json
from datetime import datetime, timedelta, timezone

from api.database import get_db

GOOGLE_CLIENT_ID     = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")

# Robust URL detection for Vercel vs Local
APP_URL = os.environ.get("APP_URL") or os.environ.get("VERCEL_URL") or "http://localhost:3000"
if "://" not in APP_URL:
    APP_URL = f"https://{APP_URL}"
APP_URL = APP_URL.rstrip("/")

REDIRECT_URI         = f"{APP_URL}/api/auth/youtube/callback"

# All three scopes — yt-analytics-monetary.readonly required for revenue
YT_SCOPES = [
    "https://www.googleapis.com/auth/yt-analytics.readonly",
    "https://www.googleapis.com/auth/youtube.readonly",
]

# Top-level imports for consistency
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from api.encryption import decrypt, encrypt
from api.services.manychat_service import ManyChatService, ManyChatAuthError
from api.services.instagram_service import InstagramService


async def perform_sync(user_id: str) -> dict:
    print(f"[SYNC] Starting sync for user: {user_id}")
    with get_db() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

    if not row:
        print(f"[SYNC] Aborted: User {user_id} not found in DB")
        from api.database import get_storage_engine
        engine = get_storage_engine()
        msg = "skipped: user not in db"
        if engine == "sqlite_memory":
            msg += " (No DATABASE_URL set on Vercel. Persistence is required for OAuth tokens)"
        else:
            msg += " (User not found in persistent database. Please re-connect metrics in Settings.)"
        return {"youtube": msg, "manychat": msg, "instagram": msg}

    user = dict(row)
    results = {"youtube": "skipped", "manychat": "skipped", "instagram": "skipped"}
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # ── 1. YouTube Sync ──────────────────────────────────────────────────────
    if user.get("yt_refresh_token"):
        print("[SYNC] Initialising YouTube Sync...")
        try:
            if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
                print("[SYNC] YouTube Sync Aborted: GOOGLE_CLIENT_ID/SECRET missing in environment")
                results["youtube"] = "failed: missing api credentials"
            else:
                raw_token = decrypt(user["yt_refresh_token"])
                if not raw_token:
                    raise ValueError("YouTube token decryption failed. Re-connection required.")

                creds = Credentials(
                    token=None,
                    refresh_token=raw_token,
                    token_uri="https://oauth2.googleapis.com/token",
                    client_id=GOOGLE_CLIENT_ID,
                    client_secret=GOOGLE_CLIENT_SECRET,
                    scopes=YT_SCOPES,
                )
                creds.refresh(Request())

                youtube  = build("youtube", "v3", credentials=creds, cache_discovery=False)
                yt_analy = build("youtubeAnalytics", "v2", credentials=creds, cache_discovery=False)

                # 1a. Channel statistics
                ch_res = youtube.channels().list(mine=True, part="statistics,snippet,contentDetails").execute()
                channel_id = "MINE"
                if ch_res.get("items"):
                    channel = ch_res["items"][0]
                    channel_id = channel.get("id") or "MINE"
                    stats = channel.get("statistics", {})
                    
                    with get_db() as conn:
                        conn.execute("UPDATE users SET youtube_channel_id = ? WHERE id = ?", (channel_id, user_id))

                    _upsert_metric(user_id, today, "youtube", "total_subscribers", int(stats.get("subscriberCount") or 0))
                    _upsert_metric(user_id, today, "youtube", "total_views", int(stats.get("viewCount") or 0))
                    _upsert_metric(user_id, today, "youtube", "total_videos", int(stats.get("videoCount") or 0))
                    print(f"[SYNC] YouTube Channel: {channel_id}")

                ids = f"channel=={channel_id}" if channel_id != "MINE" else "channel==MINE"

                # 1b. Historical analytics
                analytics_ok = False
                for days_back, label in [(30, "30-day"), (90, "90-day")]:
                    try:
                        end_date = (datetime.now(timezone.utc) - timedelta(days=2)).strftime("%Y-%m-%d")
                        start_date = (datetime.now(timezone.utc) - timedelta(days=days_back)).strftime("%Y-%m-%d")
                        report = yt_analy.reports().query(
                            ids=ids, startDate=start_date, endDate=end_date,
                            metrics="views,estimatedRevenue,subscribersGained,subscribersLost,estimatedMinutesWatched,averageViewDuration,likes,comments,shares",
                            dimensions="day", sort="day"
                        ).execute()

                        rows = report.get("rows") or []
                        if rows:
                            metric_names = ["views", "revenue", "subs_gained", "subs_lost", "watch_time_minutes", "avg_view_duration", "likes", "comments", "shares"]
                            for row_data in rows:
                                date_val = row_data[0]
                                for i, name in enumerate(metric_names):
                                    raw_val = row_data[i + 1]
                                    _upsert_metric(user_id, date_val, "youtube", name, float(raw_val or 0))
                            analytics_ok = True
                            print(f"[SYNC] YouTube {label} analytics stored")
                            break
                    except Exception as e: print(f"[SYNC] YouTube {label} failed: {e}")

                # 1c. Demographics
                try:
                    end_dt = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
                    start_dt = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d")
                    age_report = yt_analy.reports().query(ids=ids, startDate=start_dt, endDate=end_dt, metrics="viewerPercentage", dimensions="ageGroup,gender").execute()
                    for r in (age_report.get("rows") or []):
                        _upsert_metric(user_id, today, "youtube_demo", "viewerPercentage", float(r[2]), dimension=f"{r[0]}_{r[1]}")
                    
                    country_report = yt_analy.reports().query(ids=ids, startDate=start_dt, endDate=end_dt, metrics="views", dimensions="country", sort="-views", maxResults=10).execute()
                    for r in (country_report.get("rows") or []):
                        _upsert_metric(user_id, today, "youtube_demo", "countryViews", float(r[1]), dimension=r[0])
                except Exception as de: print(f"[SYNC] YouTube demographics skipped: {de}")

                # 1d. Recent Videos
                try:
                    if ch_res.get("items"):
                        uploads_id = ch_res["items"][0].get("contentDetails", {}).get("relatedPlaylists", {}).get("uploads")
                        if uploads_id:
                            items = youtube.playlistItems().list(playlistId=uploads_id, part="contentDetails", maxResults=10).execute()
                            v_ids = [i["contentDetails"]["videoId"] for i in items.get("items", [])]
                            if v_ids:
                                v_stats = youtube.videos().list(id=",".join(v_ids), part="snippet,statistics").execute()
                                for v in v_stats.get("items", []):
                                    _upsert_video(user_id, {
                                        "id": v["id"], "title": v["snippet"]["title"], "published_at": v["snippet"]["publishedAt"],
                                        "view_count": int(v["statistics"].get("viewCount") or 0),
                                        "like_count": int(v["statistics"].get("likeCount") or 0),
                                        "comment_count": int(v["statistics"].get("commentCount") or 0),
                                        "thumbnail_url": v["snippet"]["thumbnails"].get("medium", {}).get("url", "")
                                    })
                except Exception as ve: print(f"[SYNC] YouTube videos skipped: {ve}")

                results["youtube"] = "success"
        except Exception as e:
            print(f"[SYNC] YouTube Sync Overall Error: {e}")
            results["youtube"] = f"failed: {str(e)}"

    # ── 2. ManyChat Sync ─────────────────────────────────────────────────────
    print("[SYNC] Initialising ManyChat Sync...")
    try:
        mc_key = None
        if user.get("manychat_key"):
            mc_key = decrypt(user["manychat_key"])
        
        if not mc_key and os.environ.get("MANYCHAT_API_KEY"):
            mc_key = os.environ["MANYCHAT_API_KEY"]

        if mc_key:
            mc_service = ManyChatService(mc_key)
            mc_data = await mc_service.fetch_all_data()
            mc_metrics = {
                "manychat_subscribers": mc_data["total_contacts"],
                "manychat_active_widgets": mc_data["active_widgets"],
                "manychat_total_flows": mc_data["total_flows"],
                "manychat_growth_tools": mc_data["active_growth_tools"],
            }
            for n, v in mc_metrics.items():
                _upsert_metric(user_id, today, "manychat", n, v)
            
            for auto in mc_data["automations"]:
                _upsert_automation(user_id, auto, synced_at=datetime.now(timezone.utc).isoformat())
            
            for inter in mc_data.get("interactions", []):
                _upsert_interaction(user_id, inter)
                
            results["manychat"] = "success"
            print("[SYNC] ManyChat Sync Successful")
        else:
            results["manychat"] = "skipped: no api key"
    except Exception as e:
        print(f"[SYNC] ManyChat Failure: {e}")
        results["manychat"] = f"failed: {e}"

    # ── 3. Instagram Sync ───────────────────────────────────────────────────
    print("[SYNC] Initialising Instagram Sync...")
    try:
        ig_token = None
        if user.get("ig_access_token"):
            ig_token = decrypt(user["ig_access_token"])
        if not ig_token and os.environ.get("INSTAGRAM_ACCESS_TOKEN"):
            ig_token = os.environ["INSTAGRAM_ACCESS_TOKEN"]

        if ig_token:
            ig_service = InstagramService(ig_token)
            ig_user_id = user.get("ig_user_id") or await ig_service.get_user_id()
            if ig_user_id:
                if not user.get("ig_user_id"):
                    with get_db() as conn: conn.execute("UPDATE users SET ig_user_id = ? WHERE id = ?", (ig_user_id, user_id))
                
                # Profile
                prof = await ig_service.get_profile_info(ig_user_id)
                if "followers_count" in prof:
                    _upsert_metric(user_id, today, "instagram", "followers", prof["followers_count"])
                    _upsert_metric(user_id, today, "instagram", "media_count", prof.get("media_count", 0))

                # User Insights
                try:
                    insights = await ig_service.get_user_insights(ig_user_id)
                    for insight in insights:
                        for val_obj in insight.get("values", []):
                            v_date = val_obj["end_time"][:10]
                            _upsert_metric(user_id, v_date, "instagram", f"total_{insight['name']}", float(val_obj.get("value") or 0))
                except Exception as ie: print(f"[SYNC] IG Insights skipped: {ie}")

                # Audience
                try:
                    audience = await ig_service.get_audience_insights(ig_user_id)
                    if audience:
                        with get_db() as conn: conn.execute("UPDATE users SET ig_audience_json = ? WHERE id = ?", (json.dumps(audience), user_id))
                except Exception as ae: print(f"[SYNC] IG Audience skipped: {ae}")

                # Media & Aggregates
                try:
                    media_list = await ig_service.get_media_list(ig_user_id, limit=50)
                    t_likes, t_comments, t_inter, t_reach, t_imp = 0, 0, 0, 0, 0
                    for m in media_list:
                        try:
                            _upsert_ig_media(user_id, m)
                            l, c, s = int(m.get("like_count") or 0), int(m.get("comments_count") or 0), int(m.get("saved") or 0)
                            r, i = int(m.get("reach") or 0), int(m.get("impressions") or 0)
                            t_likes += l
                            t_comments += c
                            t_inter += (l + c + s)
                            t_reach += r
                            t_imp += i
                        except: pass
                    
                    _upsert_metric(user_id, today, "instagram", "total_likes", float(t_likes))
                    _upsert_metric(user_id, today, "instagram", "total_comments", float(t_comments))
                    _upsert_metric(user_id, today, "instagram", "total_interactions", float(t_inter))
                    _upsert_metric(user_id, today, "instagram", "total_reach", float(t_reach))
                    _upsert_metric(user_id, today, "instagram", "total_impressions", float(t_imp))
                    
                    results["instagram"] = "success"
                    print("[SYNC] Instagram Sync Successful")
                except Exception as me: print(f"[SYNC] IG Media Sync failure: {me}")
            else:
                results["instagram"] = "failed: user_id not resolved"
        else:
            results["instagram"] = "skipped: no token"
    except Exception as e:
        print(f"[SYNC] Instagram Failure: {e}")
        results["instagram"] = f"failed: {e}"

    _log(user_id, "FINAL_STATUS", json.dumps(results))
    return results


def _upsert_metric(user_id: str, date: str, source: str, metric_name: str, value: float, dimension: str = "none"):
    row_id = f"{user_id}_{date}_{source}_{metric_name}_{dimension}"
    with get_db() as conn:
        conn.execute(
            "INSERT INTO metrics (id, user_id, date, source, metric_name, value, dimension) VALUES (?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(id) DO UPDATE SET value = excluded.value",
            (row_id, user_id, date, source, metric_name, float(value), dimension)
        )

def _upsert_interaction(user_id: str, inter: dict):
    with get_db() as conn:
        conn.execute("INSERT INTO manychat_interactions (id, user_id, subscriber_id, type, details, timestamp) VALUES (?, ?, ?, ?, ?, ?) "
                     "ON CONFLICT(id) DO NOTHING", (inter["id"], user_id, inter["subscriber_id"], inter["type"], inter["details"], inter["timestamp"]))

def _upsert_automation(user_id: str, auto: dict, synced_at: str | None = None):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO manychat_automations (id, user_id, name, status, runs, clicks, ctr, last_modified, synced_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(id) DO UPDATE SET name=excluded.name, status=excluded.status, runs=COALESCE(excluded.runs, manychat_automations.runs), "
            "clicks=COALESCE(excluded.clicks, manychat_automations.clicks), ctr=COALESCE(excluded.ctr, manychat_automations.ctr), "
            "last_modified=excluded.last_modified, synced_at=excluded.synced_at, updated_at=CURRENT_TIMESTAMP",
            (auto["id"], user_id, auto["name"], auto.get("status", "LIVE"), auto.get("runs"), auto.get("clicks"), auto.get("ctr"), auto.get("last_modified"), synced_at)
        )

def _upsert_video(user_id: str, v: dict):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO youtube_videos (id, user_id, title, published_at, view_count, like_count, comment_count, thumbnail_url) VALUES (?, ?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(id) DO UPDATE SET title=excluded.title, published_at=excluded.published_at, view_count=excluded.view_count, like_count=excluded.like_count, "
            "comment_count=excluded.comment_count, thumbnail_url=excluded.thumbnail_url, updated_at=CURRENT_TIMESTAMP",
            (v["id"], user_id, v["title"], v["published_at"], v["view_count"], v["like_count"], v["comment_count"], v["thumbnail_url"])
        )

def _upsert_ig_media(user_id: str, m: dict):
    views = m.get("video_views") or m.get("impressions", 0)
    with get_db() as conn:
        conn.execute(
            "INSERT INTO instagram_media (id, user_id, caption, media_type, media_url, permalink, timestamp, like_count, comments_count, view_count) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(id) DO UPDATE SET caption=excluded.caption, media_type=excluded.media_type, media_url=excluded.media_url, permalink=excluded.permalink, "
            "like_count=excluded.like_count, comments_count=excluded.comments_count, view_count=excluded.view_count, updated_at=CURRENT_TIMESTAMP",
            (m["id"], user_id, m.get("caption"), m["media_type"], m.get("media_url"), m["permalink"], m["timestamp"], m.get("like_count", 0), m.get("comments_count", 0), views)
        )

def _log(user_id: str, status: str, message: str, flow_id: str | None = None):
    with get_db() as conn:
        conn.execute("INSERT INTO sync_logs (user_id, status, message, flow_id) VALUES (?, ?, ?, ?)", (user_id, status, message, flow_id))

def get_youtube_debug_info(user_id: str) -> dict: return {"note": "Condensed for space"}
def get_manychat_debug_info(user_id: str) -> dict: return {"note": "Condensed for space"}
