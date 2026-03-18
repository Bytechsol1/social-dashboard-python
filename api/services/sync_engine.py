"""Sync engine (Optimized) — YouTube + ManyChat + Instagram data sync with parallel processing."""
import os
import json
import asyncio
from dotenv import load_dotenv
load_dotenv()
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any

from api.database import get_db
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from api.encryption import decrypt
from api.services.manychat_service import ManyChatService
from api.services.instagram_service import InstagramService

GOOGLE_CLIENT_ID     = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")

APP_URL = os.environ.get("APP_URL") or os.environ.get("VERCEL_URL") or "http://localhost:3000"
if "://" not in APP_URL:
    APP_URL = f"https://{APP_URL}"
APP_URL = APP_URL.rstrip("/")

YT_SCOPES = [
    "https://www.googleapis.com/auth/yt-analytics.readonly",
    "https://www.googleapis.com/auth/youtube.readonly",
]

async def perform_sync(user_id: str) -> dict:
    print(f"[SYNC] Starting OPTIMIZED sync for user: {user_id}")
    
    with get_db() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

    if not row:
        print(f"[SYNC] Aborted: User {user_id} not found in DB")
        return {"youtube": "skipped: user not in db", "manychat": "skipped: user not in db", "instagram": "skipped: user not in db"}

    user = dict(row)
    
    # Run all three service syncs in parallel
    tasks = [
        _sync_youtube(user_id, user),
        _sync_manychat(user_id, user),
        _sync_instagram(user_id, user)
    ]
    
    results_list = await asyncio.gather(*tasks)
    
    results = {
        "youtube": results_list[0],
        "manychat": results_list[1],
        "instagram": results_list[2]
    }
    
    _log(user_id, "FINAL_STATUS", json.dumps(results))
    print(f"[SYNC] Completed optimization sync for {user_id}: {results}")
    return results

async def _sync_youtube(user_id: str, user: dict) -> str:
    if not user.get("yt_refresh_token"):
        return "skipped"
    
    print("[SYNC] Starting YouTube Async Sync...")
    try:
        if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
            return "failed: missing api credentials"
            
        raw_token = decrypt(user["yt_refresh_token"])
        if not raw_token:
            return "failed: token decryption failed"

        # Note: googleapiclient is sync, we run the heavy parts in threads to avoid blocking asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _sync_youtube_blocking, user_id, user, raw_token)
    except Exception as e:
        print(f"[SYNC] YouTube Overall Error: {e}")
        return f"failed: {str(e)}"

def _sync_youtube_blocking(user_id: str, user: dict, refresh_token: str) -> str:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    try:
        creds = Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=GOOGLE_CLIENT_ID,
            client_secret=GOOGLE_CLIENT_SECRET,
            scopes=YT_SCOPES,
        )
        creds.refresh(Request())

        youtube  = build("youtube", "v3", credentials=creds, cache_discovery=False)
        yt_analy = build("youtubeAnalytics", "v2", credentials=creds, cache_discovery=False)

        with get_db() as conn:
            # 1a. Channel statistics
            ch_res = youtube.channels().list(mine=True, part="statistics,snippet,contentDetails").execute()
            channel_id = "MINE"
            if ch_res.get("items"):
                channel = ch_res["items"][0]
                channel_id = channel.get("id") or "MINE"
                stats = channel.get("statistics", {})
                conn.execute("UPDATE users SET youtube_channel_id = ? WHERE id = ?", (channel_id, user_id))
                
                _batch_upsert_metrics(conn, user_id, today, "youtube", {
                    "total_subscribers": int(stats.get("subscriberCount") or 0),
                    "total_views": int(stats.get("viewCount") or 0),
                    "total_videos": int(stats.get("videoCount") or 0)
                })

            ids = f"channel=={channel_id}" if channel_id != "MINE" else "channel==MINE"

            # 1b. Historical analytics (consolidated)
            try:
                end_date = (datetime.now(timezone.utc) - timedelta(days=2)).strftime("%Y-%m-%d")
                start_date = (datetime.now(timezone.utc) - timedelta(days=90)).strftime("%Y-%m-%d") # Go 90 days back in one query
                # Query standard metrics (without Revenue to prevent 400 Bad Request on non-monetized channels)
                report = yt_analy.reports().query(
                    ids=ids, startDate=start_date, endDate=end_date,
                    metrics="views,subscribersGained,subscribersLost,estimatedMinutesWatched,averageViewDuration,likes,comments,shares",
                    dimensions="day", sort="day"
                ).execute()

                rows = report.get("rows") or []
                metric_names = ["views", "subs_gained", "subs_lost", "watch_time_minutes", "avg_view_duration", "likes", "comments", "shares"]
                
                # Fetch Revenue separately
                revenue_map = {}
                try:
                    rev_report = yt_analy.reports().query(
                        ids=ids, startDate=start_date, endDate=end_date,
                        metrics="estimatedRevenue", dimensions="day"
                    ).execute()
                    for rr in (rev_report.get("rows") or []):
                        revenue_map[rr[0]] = float(rr[1] or 0)
                except Exception as re:
                    print(f"[SYNC] YouTube Revenue query skipped: {re}")

                for row_data in rows:
                    date_val = row_data[0]
                    metrics_batch = {}
                    for i, name in enumerate(metric_names):
                        metrics_batch[name] = float(row_data[i + 1] or 0)
                    
                    # Merge revenue if exists
                    if date_val in revenue_map:
                        metrics_batch["revenue"] = revenue_map[date_val]
                    else:
                        metrics_batch["revenue"] = 0.0
                        
                    _batch_upsert_metrics(conn, user_id, date_val, "youtube", metrics_batch)
            except Exception as e: print(f"[SYNC] YouTube Analytics block failed: {e}")

            # 1c. Demographics
            try:
                end_dt = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
                start_dt = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d")
                age_report = yt_analy.reports().query(ids=ids, startDate=start_dt, endDate=end_dt, metrics="viewerPercentage", dimensions="ageGroup,gender").execute()
                for r in (age_report.get("rows") or []):
                    _batch_upsert_metrics(conn, user_id, today, "youtube_demo", {"viewerPercentage": float(r[2])}, dimension=f"{r[0]}_{r[1]}")
                
                country_report = yt_analy.reports().query(ids=ids, startDate=start_dt, endDate=end_dt, metrics="views", dimensions="country", sort="-views", maxResults=10).execute()
                for r in (country_report.get("rows") or []):
                    _batch_upsert_metrics(conn, user_id, today, "youtube_demo", {"countryViews": float(r[1])}, dimension=r[0])
                    
                # Traffic Sources
                traffic_report = yt_analy.reports().query(ids=ids, startDate=start_dt, endDate=end_dt, metrics="views", dimensions="insightTrafficSourceType", sort="-views").execute()
                for r in (traffic_report.get("rows") or []):
                    _batch_upsert_metrics(conn, user_id, today, "youtube_demo", {"trafficSource": float(r[1])}, dimension=r[0])
            except Exception as de: print(f"[SYNC] YouTube demographics skipped: {de}")

            # 1d. Recent Videos
            try:
                if ch_res.get("items"):
                    uploads_id = ch_res["items"][0].get("contentDetails", {}).get("relatedPlaylists", {}).get("uploads")
                    print(f"[SYNC] YouTube Uploads Playlist: {uploads_id}")
                    if uploads_id:
                        items = youtube.playlistItems().list(playlistId=uploads_id, part="contentDetails", maxResults=10).execute()
                        v_ids = [i["contentDetails"]["videoId"] for i in items.get("items", [])]
                        print(f"[SYNC] Found {len(v_ids)} video IDs: {v_ids}")
                        if v_ids:
                            v_stats = youtube.videos().list(id=",".join(v_ids), part="snippet,statistics,contentDetails").execute()
                            for v in v_stats.get("items", []):
                                duration_str = v.get("contentDetails", {}).get("duration", "")
                                seconds = _parse_duration_to_seconds(duration_str)
                                
                                # Skip videos under 2 minutes (120 seconds) - treating them as Shorts
                                if 0 < seconds < 122:
                                    print(f"[SYNC] Skipping Short ({seconds}s): {v['id']} - {v['snippet']['title']}")
                                    continue
                                    
                                print(f"[SYNC] Upserting video: {v['id']} - {v['snippet']['title']}")
                                _upsert_video_conn(conn, user_id, {
                                    "id": v["id"], "title": v["snippet"]["title"], "published_at": v["snippet"]["publishedAt"],
                                    "view_count": int(v["statistics"].get("viewCount") or 0),
                                    "like_count": int(v["statistics"].get("likeCount") or 0),
                                    "comment_count": int(v["statistics"].get("commentCount") or 0),
                                    "thumbnail_url": v["snippet"]["thumbnails"].get("medium", {}).get("url", "")
                                })
                else:
                    print("[SYNC] No YouTube channel found items.")
            except Exception as ve: print(f"[SYNC] YouTube videos skipped: {ve}")

        return "success"
    except Exception as e:
        print(f"[SYNC] YouTube Blocking Error: {e}")
        return f"failed: {str(e)}"

async def _sync_manychat(user_id: str, user: dict) -> str:
    print("[SYNC] Starting ManyChat Async Sync...")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    try:
        mc_key = None
        if user.get("manychat_key"):
            mc_key = decrypt(user["manychat_key"])
        if not mc_key and os.environ.get("MANYCHAT_API_KEY"):
            mc_key = os.environ["MANYCHAT_API_KEY"]

        if not mc_key:
            return "skipped: no api key"

        mc_service = ManyChatService(mc_key)
        mc_data = await mc_service.fetch_all_data()

        with get_db() as conn:
            _batch_upsert_metrics(conn, user_id, today, "manychat", {
                "manychat_subscribers": mc_data["total_contacts"],
                "manychat_active_widgets": mc_data["active_widgets"],
                "manychat_total_flows": mc_data["total_flows"],
                "manychat_growth_tools": mc_data["active_growth_tools"],
            })
            
            # Use same connection for sub-entities
            for auto in mc_data["automations"]:
                _upsert_automation_conn(conn, user_id, auto, synced_at=datetime.now(timezone.utc).isoformat())
            
            for inter in mc_data.get("interactions", []):
                _upsert_interaction_conn(conn, user_id, inter)
                
        return "success"
    except Exception as e:
        print(f"[SYNC] ManyChat Failure: {e}")
        return f"failed: {e}"

async def _sync_instagram(user_id: str, user: dict) -> str:
    print("[SYNC] Starting Instagram Async Sync...")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    try:
        ig_token = None
        if user.get("ig_access_token"):
            ig_token = decrypt(user["ig_access_token"])
        if not ig_token and os.environ.get("INSTAGRAM_ACCESS_TOKEN"):
            ig_token = os.environ["INSTAGRAM_ACCESS_TOKEN"]

        if not ig_token: return "skipped: no token"

        ig_service = InstagramService(ig_token)
        try:
            ig_user_id = user.get("ig_user_id") or await ig_service.get_user_id()
            if not ig_user_id: return "failed: user_id not resolved"

            # Parallelize IG fetches
            profile_task = ig_service.get_profile_info(ig_user_id)
            insights_task = ig_service.get_user_insights(ig_user_id)
            audience_task = ig_service.get_audience_insights(ig_user_id)
            media_task = ig_service.get_media_list(ig_user_id, limit=50)

            prof, insights, audience, media_list = await asyncio.gather(profile_task, insights_task, audience_task, media_task)

            with get_db() as conn:
                if not user.get("ig_user_id"):
                    conn.execute("UPDATE users SET ig_user_id = ? WHERE id = ?", (ig_user_id, user_id))

                # Batch write profile/insights
                ig_metrics = {}
                if "followers_count" in prof:
                    ig_metrics["followers"] = prof["followers_count"]
                    ig_metrics["media_count"] = prof.get("media_count", 0)

                for insight in insights:
                    for val_obj in insight.get("values", []):
                        v_date = val_obj["end_time"][:10]
                        _batch_upsert_metrics(conn, user_id, v_date, "instagram", {f"total_{insight['name']}": float(val_obj.get("value") or 0)})

                if audience:
                    conn.execute("UPDATE users SET ig_audience_json = ? WHERE id = ?", (json.dumps(audience), user_id))

                # Media processing
                t_likes, t_comments, t_inter, t_reach, t_imp = 0, 0, 0, 0, 0
                for m in media_list:
                    _upsert_ig_media_conn(conn, user_id, m)
                    l, c, s = int(m.get("like_count") or 0), int(m.get("comments_count") or 0), int(m.get("saved") or 0)
                    r, i = int(m.get("reach") or 0), int(m.get("impressions") or 0)
                    t_likes += l; t_comments += c; t_inter += (l+c+s); t_reach += r; t_imp += i

                ig_metrics.update({
                    "total_likes": float(t_likes),
                    "total_comments": float(t_comments),
                    "total_interactions": float(t_inter),
                    "total_reach": float(t_reach),
                    "total_impressions": float(t_imp)
                })
                _batch_upsert_metrics(conn, user_id, today, "instagram", ig_metrics)

            return "success"
        finally:
            await ig_service.close()
    except Exception as e:
        print(f"[SYNC] Instagram Failure: {e}")
        return f"failed: {e}"

def _parse_duration_to_seconds(duration_str: str) -> int:
    """Parse ISO 8601 duration string (e.g., PT1M30S) to seconds."""
    if not duration_str:
        return 0
    import re
    match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration_str)
    if not match:
        return 0
    h, m, s = match.groups()
    hours = int(h) if h else 0
    minutes = int(m) if m else 0
    seconds = int(s) if s else 0
    return hours * 3600 + minutes * 60 + seconds

def _parse_duration_to_seconds(duration_str: str) -> int:
    """Parse ISO 8601 duration string (e.g., PT1M30S) to seconds."""
    if not duration_str:
        return 0
    import re
    match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration_str)
    if not match:
        return 0
    h, m, s = match.groups()
    hours = int(h) if h else 0
    minutes = int(m) if m else 0
    seconds = int(s) if s else 0
    return hours * 3600 + minutes * 60 + seconds

# --- Internal Database Helpers (Connection Reusing) ---

def _batch_upsert_metrics(conn, user_id: str, date: str, source: str, metrics: Dict[str, float], dimension: str = "none"):
    """Optimized metrics upsert using a single loop over an existing connection."""
    for name, val in metrics.items():
        row_id = f"{user_id}_{date}_{source}_{name}_{dimension}"
        conn.execute(
            "INSERT INTO metrics (id, user_id, date, source, metric_name, value, dimension) VALUES (?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(id) DO UPDATE SET value = excluded.value",
            (row_id, user_id, date, source, name, float(val), dimension)
        )

def _upsert_interaction_conn(conn, user_id: str, inter: dict):
    conn.execute("INSERT INTO manychat_interactions (id, user_id, subscriber_id, type, details, timestamp) VALUES (?, ?, ?, ?, ?, ?) "
                 "ON CONFLICT(id) DO NOTHING", (inter["id"], user_id, inter["subscriber_id"], inter["type"], inter["details"], inter["timestamp"]))

def _upsert_automation_conn(conn, user_id: str, auto: dict, synced_at: str | None = None):
    conn.execute(
        "INSERT INTO manychat_automations (id, user_id, name, status, runs, clicks, ctr, last_modified, synced_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) "
        "ON CONFLICT(id) DO UPDATE SET name=excluded.name, status=excluded.status, runs=COALESCE(excluded.runs, manychat_automations.runs), "
        "clicks=COALESCE(excluded.clicks, manychat_automations.clicks), ctr=COALESCE(excluded.ctr, manychat_automations.ctr), "
        "last_modified=excluded.last_modified, synced_at=excluded.synced_at, updated_at=CURRENT_TIMESTAMP",
        (auto["id"], user_id, auto["name"], auto.get("status", "LIVE"), auto.get("runs"), auto.get("clicks"), auto.get("ctr"), auto.get("last_modified"), synced_at)
    )

def _upsert_video_conn(conn, user_id: str, v: dict):
    conn.execute(
        "INSERT INTO youtube_videos (id, user_id, title, published_at, view_count, like_count, comment_count, thumbnail_url) VALUES (?, ?, ?, ?, ?, ?, ?, ?) "
        "ON CONFLICT(id) DO UPDATE SET title=excluded.title, published_at=excluded.published_at, view_count=excluded.view_count, like_count=excluded.like_count, "
        "comment_count=excluded.comment_count, thumbnail_url=excluded.thumbnail_url, updated_at=CURRENT_TIMESTAMP",
        (v["id"], user_id, v["title"], v["published_at"], v["view_count"], v["like_count"], v["comment_count"], v["thumbnail_url"])
    )

def _upsert_ig_media_conn(conn, user_id: str, m: dict):
    views = m.get("video_views") or m.get("impressions", 0)
    conn.execute(
        "INSERT INTO instagram_media (id, user_id, caption, media_type, media_url, permalink, timestamp, like_count, comments_count, view_count) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
        "ON CONFLICT(id) DO UPDATE SET caption=excluded.caption, media_type=excluded.media_type, media_url=excluded.media_url, permalink=excluded.permalink, "
        "like_count=excluded.like_count, comments_count=excluded.comments_count, view_count=excluded.view_count, updated_at=CURRENT_TIMESTAMP",
        (m["id"], user_id, m.get("caption"), m["media_type"], m.get("media_url"), m["permalink"], m["timestamp"], m.get("like_count", 0), m.get("comments_count", 0), views)
    )

def _log(user_id: str, status: str, message: str, flow_id: str | None = None):
    """Defensive logging that never crashes the main process."""
    try:
        with get_db() as conn:
            try:
                conn.execute(
                    "INSERT INTO sync_logs (user_id, status, message, flow_id) VALUES (?, ?, ?, ?)", 
                    (user_id, status, message, flow_id)
                )
            except Exception as e:
                error_str = str(e)
                if "duplicate key" in error_str or "23505" in error_str:
                    # Postgres SERIAL sequence is out of sync — reset it and retry
                    try:
                        conn.rollback() # Clear aborted state
                        conn.execute("SELECT setval('sync_logs_id_seq', (SELECT COALESCE(MAX(id), 0) + 1 FROM sync_logs), false)")
                        conn.execute(
                            "INSERT INTO sync_logs (user_id, status, message, flow_id) VALUES (?, ?, ?, ?)", 
                            (user_id, status, message, flow_id)
                        )
                    except Exception:
                        pass # Still failed? Give up on logging this one
                else:
                    # Other DB error? Rollback so get_db's __exit__ doesn't fail on commit
                    conn.rollback()
                    print(f"[SYNC LOG ERROR] {e}")
    except Exception as e:
        # Catch errors from get_db itself (e.g. connection issues)
        print(f"[CRITICAL LOG ERROR] {e}")

