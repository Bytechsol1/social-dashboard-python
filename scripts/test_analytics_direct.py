import os
from datetime import datetime, timedelta, timezone
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from api.database import get_db
from dotenv import load_dotenv

load_dotenv()

def test_analytics():
    with get_db() as conn:
        # Load single user row
        user_row = conn.execute("SELECT * FROM users LIMIT 1").fetchone()
        if not user_row:
            print("No users found in database!")
            return
            
        user = dict(user_row)
        print("Columns in users table:", user.keys())
        
        user_id = user["id"]
        refresh_token = user.get("yt_refresh_token")
        
        print(f"--- Testing Analytics for User: {user_id} ---")
        if not refresh_token:
            print("Skipping: No refresh token found!")
            return
            
        # Initialize credentials with refresh_token directly
        creds = Credentials(
            None, 
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=os.environ.get("GOOGLE_CLIENT_ID"),
            client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
            scopes=["https://www.googleapis.com/auth/youtube.readonly", "https://www.googleapis.com/auth/yt-analytics.readonly"]
        )
        
        try:
            # 1. Get Channel ID
            youtube = build("youtube", "v3", credentials=creds, cache_discovery=False)
            ch_res = youtube.channels().list(part="id,statistics", mine=True).execute()
            if not ch_res.get("items"):
                print("No Channel found for this user.")
                return
                
            channel_id = ch_res["items"][0]["id"]
            stats = ch_res["items"][0]["statistics"]
            print(f"Channel ID: {channel_id}")
            print(f"Total Views (Data API): {stats.get('viewCount')}")
            
            # 2. Run Analytics Query
            yt_analy = build("youtubeAnalytics", "v2", credentials=creds, cache_discovery=False)
            end_date = (datetime.now(timezone.utc) - timedelta(days=2)).strftime("%Y-%m-%d")
            start_date = (datetime.now(timezone.utc) - timedelta(days=90)).strftime("%Y-%m-%d")
            
            ids = f"channel=={channel_id}"
            print(f"Querying IDs: {ids} | Range: {start_date} to {end_date}")
            
            report = yt_analy.reports().query(
                ids=ids, startDate=start_date, endDate=end_date,
                metrics="views,estimatedRevenue,subscribersGained,subscribersLost,estimatedMinutesWatched,averageViewDuration,likes,comments,shares",
                dimensions="day", sort="day"
            ).execute()
            
            print("RAW REPORT ROWS:")
            rows = report.get("rows") or []
            for r in rows[:5]: # print first 5
                print(r)
            if not rows:
                print("EMPTY ROWS RETURNED FROM ANALYTICS API!")
                
        except Exception as e:
            print(f"Query failed with error: {e}")

if __name__ == "__main__":
    test_analytics()
