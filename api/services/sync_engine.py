"""Sync engine — YouTube + ManyChat data sync with full diagnostics."""
import os
import json
from datetime import datetime, timedelta, timezone

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

from api.database import get_db
from api.encryption import decrypt
from api.services.manychat_service import ManyChatService, ManyChatAuthError

GOOGLE_CLIENT_ID     = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
APP_URL              = os.environ.get("APP_URL", "http://localhost:3000").rstrip("/")
REDIRECT_URI         = f"{APP_URL}/api/auth/youtube/callback"

# All three scopes — yt-analytics-monetary.readonly required for revenue
YT_SCOPES = [
    "https://www.googleapis.com/auth/yt-analytics.readonly",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics-monetary.readonly",
]


async def perform_sync(user_id: str) -> dict:
    print(f"[SYNC] Starting sync for user: {user_id}")
    with get_db() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

    if not row:
        print(f"[SYNC] Aborted: User {user_id} not found in DB")
        return {"youtube": "skipped", "manychat": "skipped"}

    user = dict(row)
    results = {"youtube": "skipped", "manychat": "skipped"}

    # ── 1. YouTube Sync ──────────────────────────────────────────────────────
    if user.get("yt_refresh_token"):
        print("[SYNC] Initialising YouTube Sync...")
        try:
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

            # 1a. Channel statistics (real-time)
            ch_res = youtube.channels().list(
                mine=True, part="statistics,snippet,contentDetails"
            ).execute()

            channel_id = "MINE"
            if ch_res.get("items"):
                channel    = ch_res["items"][0]
                channel_id = channel.get("id") or "MINE"
                stats      = channel.get("statistics", {})
                today      = datetime.now(timezone.utc).strftime("%Y-%m-%d")

                # Store channel_id for future API calls & debugging
                with get_db() as conn:
                    conn.execute(
                        "UPDATE users SET youtube_channel_id = ? WHERE id = ?",
                        (channel_id, user_id)
                    )

                _upsert_metric(user_id, today, "youtube", "total_subscribers",
                               int(stats.get("subscriberCount") or 0))
                _upsert_metric(user_id, today, "youtube", "total_views",
                               int(stats.get("viewCount") or 0))
                _upsert_metric(user_id, today, "youtube", "total_videos",
                               int(stats.get("videoCount") or 0))
                print(f"[SYNC] Channel ID: {channel_id}, Subs: {stats.get('subscriberCount')}")

            ids = f"channel=={channel_id}" if channel_id != "MINE" else "channel==MINE"

            # 1b. Historical analytics — try 30d, 90d, then 28d fallback
            analytics_ok = False
            for days_back, label in [(30, "30-day"), (90, "90-day"), (28, "28-day")]:
                try:
                    end_date   = (datetime.now(timezone.utc) - timedelta(days=2)).strftime("%Y-%m-%d")
                    start_date = (datetime.now(timezone.utc) - timedelta(days=days_back)).strftime("%Y-%m-%d")

                    report = yt_analy.reports().query(
                        ids=ids,
                        startDate=start_date,
                        endDate=end_date,
                        metrics=(
                            "views,estimatedRevenue,subscribersGained,subscribersLost,"
                            "estimatedMinutesWatched,averageViewDuration,likes,comments,shares"
                        ),
                        dimensions="day",
                        sort="day",
                    ).execute()

                    print(f"[SYNC] YouTube {label} raw response: "
                          f"columnHeaders={report.get('columnHeaders')}, "
                          f"rows_count={len(report.get('rows') or [])}")

                    rows = report.get("rows") or []
                    if rows:
                        # Metric names must match what api.py queries!
                        metric_names = [
                            "views",            # daily YouTube views
                            "revenue",          # estimatedRevenue
                            "subs_gained",      # subscribersGained
                            "subs_lost",        # subscribersLost
                            "watch_time_minutes",  # estimatedMinutesWatched (KEY FIX)
                            "avg_view_duration",   # averageViewDuration in seconds
                            "likes",
                            "comments",
                            "shares",
                        ]
                        for row_data in rows:
                            date_val = row_data[0]
                            for i, name in enumerate(metric_names):
                                raw_val = row_data[i + 1]
                                # Store as float — never truncate watch_time to int
                                _upsert_metric(user_id, date_val, "youtube", name,
                                               float(raw_val) if raw_val is not None else 0.0)
                        analytics_ok = True
                        print(f"[SYNC] YouTube {label} analytics: {len(rows)} rows stored")
                        break
                    else:
                        print(f"[SYNC] YouTube {label} analytics returned 0 rows, trying wider range...")
                except Exception as e:
                    print(f"[SYNC] YouTube {label} analytics failed: {e}")

            if not analytics_ok:
                _log(user_id, "WARNING",
                     "YouTube historical analytics returned no data for any date range. "
                     "Check OAuth scopes and channel age.")

            # 1c. Demographic analytics — age/gender breakdown
            try:
                end_date   = (datetime.now(timezone.utc) - timedelta(days=2)).strftime("%Y-%m-%d")
                start_date = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d")
                today      = datetime.now(timezone.utc).strftime("%Y-%m-%d")

                # Age/gender breakdown
                age_report = yt_analy.reports().query(
                    ids=ids,
                    startDate=start_date,
                    endDate=end_date,
                    metrics="viewerPercentage",
                    dimensions="ageGroup,gender",
                ).execute()

                for row_data in (age_report.get("rows") or []):
                    age_group, gender, percentage = row_data[0], row_data[1], row_data[2]
                    dim_key = f"{age_group}_{gender}"
                    _upsert_metric(user_id, today, "youtube_demo", "viewerPercentage",
                                   float(percentage), dimension=dim_key)

                # Country breakdown
                country_report = yt_analy.reports().query(
                    ids=ids,
                    startDate=start_date,
                    endDate=end_date,
                    metrics="views",
                    dimensions="country",
                    sort="-views",
                    maxResults=10,
                ).execute()

                for row_data in (country_report.get("rows") or []):
                    country, views = row_data[0], row_data[1]
                    _upsert_metric(user_id, today, "youtube_demo", "countryViews",
                                   float(views), dimension=country)

                # Subscriber gain/loss timeseries
                sub_report = yt_analy.reports().query(
                    ids=ids,
                    startDate=start_date,
                    endDate=end_date,
                    metrics="subscribersGained,subscribersLost,averageViewDuration,averageViewPercentage",
                    dimensions="day",
                    sort="day",
                ).execute()

                for row_data in (sub_report.get("rows") or []):
                    date_val = row_data[0]
                    _upsert_metric(user_id, date_val, "youtube_demo", "subscribersGained",
                                   float(row_data[1] or 0))
                    _upsert_metric(user_id, date_val, "youtube_demo", "subscribersLost",
                                   float(row_data[2] or 0))
                    _upsert_metric(user_id, date_val, "youtube_demo", "avgViewDuration",
                                   float(row_data[3] or 0))
                    _upsert_metric(user_id, date_val, "youtube_demo", "avgViewPercentage",
                                   float(row_data[4] or 0))

                print("[SYNC] YouTube demographic analytics stored")
            except Exception as demo_err:
                print(f"[SYNC] YouTube demographic analytics failed (non-fatal): {demo_err}")
                _log(user_id, "WARNING", f"Demographic analytics failed: {demo_err}")

            # 1d. Recent Videos
            try:
                if ch_res.get("items"):
                    playlist_id = ch_res["items"][0].get("contentDetails", {}).get(
                        "relatedPlaylists", {}
                    ).get("uploads")
                    if playlist_id:
                        playlist_items = youtube.playlistItems().list(
                            playlistId=playlist_id, part="snippet,contentDetails", maxResults=10
                        ).execute()
                        video_ids = [
                            item["contentDetails"]["videoId"]
                            for item in playlist_items.get("items", [])
                        ]
                        if video_ids:
                            video_stats = youtube.videos().list(
                                id=",".join(video_ids), part="snippet,statistics"
                            ).execute()
                            for vid in video_stats.get("items", []):
                                _upsert_video(user_id, {
                                    "id":            vid["id"],
                                    "title":         vid["snippet"]["title"],
                                    "published_at":  vid["snippet"]["publishedAt"],
                                    "view_count":    int(vid["statistics"].get("viewCount") or 0),
                                    "like_count":    int(vid["statistics"].get("likeCount") or 0),
                                    "comment_count": int(vid["statistics"].get("commentCount") or 0),
                                    "thumbnail_url": (
                                        vid["snippet"]["thumbnails"]
                                        .get("medium", vid["snippet"]["thumbnails"].get("default", {}))
                                        .get("url", "")
                                    ),
                                })
                            print(f"[SYNC] Stored {len(video_stats.get('items', []))} videos")
            except Exception as video_err:
                print(f"[SYNC] YouTube video sync failed (non-fatal): {video_err}")

            results["youtube"] = "success"
            _log(user_id, "COMPLETED", "YouTube sync successful.")

        except Exception as err:
            err_msg = str(err)
            print(f"[SYNC] YT Error: {err_msg}")
            results["youtube"] = f"failed: {err_msg}"
            _log(user_id, "FAILED", f"YouTube Connection Error: {err_msg}")

    # ── 2. ManyChat Sync ─────────────────────────────────────────────────────
    print("[SYNC] Initialising ManyChat Sync...")
    mc_key = None
    try:
        if user.get("manychat_key"):
            mc_key = decrypt(user["manychat_key"])
            if not mc_key:
                _log(user_id, "ERROR",
                     "ManyChat key found but decryption returned empty — key mismatch?")
    except Exception as e:
        print(f"[SYNC] ManyChat Key decryption failed: {e}")
        _log(user_id, "ERROR", f"ManyChat Decryption Error: {str(e)}")
        mc_key = None

    if not mc_key and os.environ.get("MANYCHAT_API_KEY"):
        mc_key = os.environ["MANYCHAT_API_KEY"]

    if mc_key:
        try:
            mc_service = ManyChatService(mc_key)
            mc_data    = await mc_service.fetch_all_data()
            today      = datetime.now(timezone.utc).strftime("%Y-%m-%d")

            # Store aggregate metrics with CORRECT metric names
            mc_metrics = {
                "manychat_subscribers":     mc_data["total_contacts"],      # explicitly named
                "manychat_active_widgets":  mc_data["active_widgets"],
                "manychat_conversion_rate": mc_data["lead_conversion_rate"],
                "manychat_total_tags":      mc_data["total_tags"],
                "manychat_total_flows":     mc_data["total_flows"],
                "manychat_growth_tools":    mc_data["active_growth_tools"],
            }
            for name, value in mc_metrics.items():
                _upsert_metric(user_id, today, "manychat", name, value)

            # Store automations — runs/ctr are None (not available from API)
            now_utc = datetime.now(timezone.utc).isoformat()
            automations = mc_data["automations"]
            for auto in automations:
                _upsert_automation(user_id, auto, synced_at=now_utc)

            # Store interactions
            interactions = mc_data.get("interactions", [])
            for inter in interactions:
                _upsert_interaction(user_id, inter)

            _log(user_id, "COMPLETED",
                 f"ManyChat sync: {len(automations)} flows, {len(interactions)} interactions. "
                 "Note: runs/CTR not available from public API.")
            print("[SYNC] ManyChat Sync Successful.")
            results["manychat"] = "success"

        except ManyChatAuthError as auth_err:
            err_msg = str(auth_err)
            print(f"[SYNC] ManyChat Auth Error: {err_msg}")
            _log(user_id, "FAILED", f"ManyChat Auth Failure: {err_msg}")
            results["manychat"] = f"auth_failed: {err_msg}"
        except Exception as error:
            err_msg = str(error)
            print(f"[SYNC] ManyChat Sync Error: {err_msg}")
            _log(user_id, "FAILED", f"ManyChat Failure: {err_msg}")
            results["manychat"] = f"failed: {err_msg}"
    else:
        print("[SYNC] ManyChat Sync Skipped: No API key found.")
        results["manychat"] = "skipped: no api key"

    _log(user_id, "FINAL_STATUS", json.dumps(results))
    print(f"[SYNC] Complete for {user_id}. Results: {results}")
    return results


# ── Diagnostic helpers ────────────────────────────────────────────────────────

def get_youtube_debug_info(user_id: str) -> dict:
    """Returns token status, scopes, channel info, and raw 7-day API response."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT yt_refresh_token, youtube_channel_id FROM users WHERE id = ?",
            (user_id,)
        ).fetchone()

    if not row or not row["yt_refresh_token"]:
        return {"error": "No YouTube token stored", "user_id": user_id}

    raw_token = decrypt(row["yt_refresh_token"])
    if not raw_token:
        return {
            "error": "Token decryption failed — ENCRYPTION_SECRET mismatch?",
            "user_id": user_id,
        }

    stored_channel_id = row["youtube_channel_id"]

    try:
        creds = Credentials(
            token=None,
            refresh_token=raw_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=GOOGLE_CLIENT_ID,
            client_secret=GOOGLE_CLIENT_SECRET,
            scopes=YT_SCOPES,
        )
        creds.refresh(Request())

        # Inspect which scopes were actually granted
        granted_scopes = list(creds.scopes or YT_SCOPES)

        youtube  = build("youtube", "v3", credentials=creds, cache_discovery=False)
        yt_analy = build("youtubeAnalytics", "v2", credentials=creds, cache_discovery=False)

        ch_res = youtube.channels().list(mine=True, part="statistics,snippet").execute()
        api_channel_id = None
        channel_info = {}
        if ch_res.get("items"):
            ch = ch_res["items"][0]
            api_channel_id = ch.get("id")
            channel_info = {
                "id":    api_channel_id,
                "title": ch["snippet"].get("title"),
                "subs":  ch["statistics"].get("subscriberCount"),
                "views": ch["statistics"].get("viewCount"),
                "created": ch["snippet"].get("publishedAt"),
            }

        ids        = f"channel=={api_channel_id}" if api_channel_id else "channel==MINE"
        end_date   = (datetime.now(timezone.utc) - timedelta(days=2)).strftime("%Y-%m-%d")
        start_date = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d")

        try:
            report = yt_analy.reports().query(
                ids=ids,
                startDate=start_date,
                endDate=end_date,
                metrics="views,estimatedMinutesWatched,subscribersGained",
                dimensions="day",
                sort="day",
            ).execute()
            analytics_raw = report
        except Exception as ae:
            analytics_raw = {"error": str(ae)}

        return {
            "user_id":              user_id,
            "token_valid":          True,
            "scopes_requested":     YT_SCOPES,
            "scopes_granted":       granted_scopes,
            "channel_stored_in_db": stored_channel_id,
            "channel_from_api":     api_channel_id,
            "channel_id_mismatch":  stored_channel_id != api_channel_id,
            "channel":              channel_info,
            "date_range":           {"start": start_date, "end": end_date},
            "analytics_raw":        analytics_raw,
            "analytics_rows_count": len(analytics_raw.get("rows") or []),
        }
    except Exception as e:
        return {
            "user_id":     user_id,
            "token_valid": False,
            "error":       str(e),
        }


def get_manychat_debug_info(user_id: str) -> dict:
    """Returns DB snapshot vs live ManyChat API side-by-side."""
    import asyncio

    with get_db() as conn:
        row      = conn.execute(
            "SELECT manychat_key FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        db_autos = [dict(r) for r in conn.execute(
            "SELECT id, name, runs, ctr, last_modified, synced_at, updated_at "
            "FROM manychat_automations WHERE user_id = ? ORDER BY last_modified DESC LIMIT 15",
            (user_id,)
        ).fetchall()]
        db_metrics = [dict(r) for r in conn.execute(
            "SELECT metric_name, value, date FROM metrics "
            "WHERE user_id = ? AND source = 'manychat' ORDER BY date DESC LIMIT 20",
            (user_id,)
        ).fetchall()]

    if not row or not row["manychat_key"]:
        return {
            "error":           "No ManyChat key stored",
            "db_automations":  db_autos,
            "db_metrics":      db_metrics,
        }

    mc_key = decrypt(row["manychat_key"])
    if not mc_key:
        return {
            "error":          "Key decryption failed",
            "db_automations": db_autos,
        }

    try:
        mc_service = ManyChatService(mc_key)
        live_data  = asyncio.run(mc_service.fetch_live_comparison())
        return {
            "user_id":         user_id,
            "db_automations":  db_autos,
            "db_metrics":      db_metrics,
            "live_api":        live_data,
            "discrepancy_note": (
                "runs and ctr in DB are NULL because ManyChat public API "
                "does not expose flow analytics. These values cannot be "
                "retrieved programmatically."
            ),
        }
    except Exception as e:
        return {
            "user_id":        user_id,
            "error":          str(e),
            "db_automations": db_autos,
        }


# ── DB helpers ────────────────────────────────────────────────────────────────

def _upsert_metric(
    user_id: str, date: str, source: str,
    metric_name: str, value: float, dimension: str = "none"
):
    row_id = f"{user_id}_{date}_{source}_{metric_name}_{dimension}"
    with get_db() as conn:
        conn.execute(
            "INSERT INTO metrics (id, user_id, date, source, metric_name, value, dimension) "
            "VALUES (?, ?, ?, ?, ?, ?, ?) ON CONFLICT(id) DO UPDATE SET value = excluded.value",
            (row_id, user_id, date, source, metric_name, float(value), dimension)
        )


def _upsert_interaction(user_id: str, inter: dict):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO manychat_interactions "
            "(id, user_id, subscriber_id, type, details, timestamp) "
            "VALUES (?, ?, ?, ?, ?, ?) ON CONFLICT(id) DO NOTHING",
            (
                inter["id"], user_id, inter["subscriber_id"],
                inter["type"], inter["details"], inter["timestamp"]
            )
        )


def _upsert_automation(user_id: str, auto: dict, synced_at: str | None = None):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO manychat_automations "
            "(id, user_id, name, status, runs, clicks, ctr, last_modified, synced_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(id) DO UPDATE SET "
            "name=excluded.name, status=excluded.status, "
            "runs=COALESCE(excluded.runs, manychat_automations.runs), "
            "clicks=COALESCE(excluded.clicks, manychat_automations.clicks), "
            "ctr=COALESCE(excluded.ctr, manychat_automations.ctr), "
            "last_modified=excluded.last_modified, "
            "synced_at=excluded.synced_at, updated_at=CURRENT_TIMESTAMP",
            (
                auto["id"], user_id, auto["name"], auto.get("status", "LIVE"),
                auto.get("runs"),
                auto.get("clicks"),
                auto.get("ctr"),
                auto.get("last_modified"),
                synced_at,
            )
        )


def _upsert_video(user_id: str, video: dict):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO youtube_videos "
            "(id, user_id, title, published_at, view_count, like_count, comment_count, thumbnail_url) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(id) DO UPDATE SET "
            "title=excluded.title, published_at=excluded.published_at, "
            "view_count=excluded.view_count, like_count=excluded.like_count, "
            "comment_count=excluded.comment_count, thumbnail_url=excluded.thumbnail_url, "
            "updated_at=CURRENT_TIMESTAMP",
            (
                video["id"], user_id, video["title"], video["published_at"],
                video["view_count"], video["like_count"],
                video["comment_count"], video["thumbnail_url"]
            )
        )


def _log(user_id: str, status: str, message: str, flow_id: str | None = None):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO sync_logs (user_id, status, message, flow_id) VALUES (?, ?, ?, ?)",
            (user_id, status, message, flow_id)
        )
