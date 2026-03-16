import os
import json
import asyncio
from typing import List, Dict, Any
from api.database import get_db
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from api.encryption import decrypt

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")

def _get_creds(user_id: str) -> Credentials:
    with get_db() as conn:
        row = conn.execute("SELECT yt_refresh_token FROM users WHERE id = ?", (user_id,)).fetchone()
        if not row or not row.get("yt_refresh_token"):
            raise Exception("YouTube connection missing or token unset")
        
        refresh_token = decrypt(row["yt_refresh_token"])
        creds = Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=GOOGLE_CLIENT_ID,
            client_secret=GOOGLE_CLIENT_SECRET
        )
        creds.refresh(Request())
        return creds

def fetch_comments_blocking(user_id: str) -> List[Dict[str, Any]]:
    creds = _get_creds(user_id)
    youtube = build("youtube", "v3", credentials=creds, cache_discovery=False)
    
    # 1. Get channel ID
    with get_db() as conn:
        row = conn.execute("SELECT youtube_channel_id FROM users WHERE id = ?", (user_id,)).fetchone()
        channel_id = row["youtube_channel_id"] if row else None
        
    if not channel_id:
        ch_res = youtube.channels().list(mine=True, part="id").execute()
        if ch_res.get("items"):
            channel_id = ch_res["items"][0]["id"]
            with get_db() as conn:
                conn.execute("UPDATE users SET youtube_channel_id = ? WHERE id = ?", (channel_id, user_id))
                
    if not channel_id:
        raise Exception("Could not resolve YouTube Channel ID")

    # 2. List comment threads
    res = youtube.commentThreads().list(
        allThreadsRelatedToChannelId=channel_id,
        part="snippet,replies",
        maxResults=30
    ).execute()
    
    formatted = []
    for item in res.get("items", []):
        snippet = item.get("snippet", {})
        top_comment = snippet.get("topLevelComment", {}).get("snippet", {})
        
        formatted.append({
            "id": item["id"],
            "top_comment": {
                "id": snippet.get("topLevelComment", {}).get("id"),
                "author": top_comment.get("authorDisplayName"),
                "author_avatar": top_comment.get("authorProfileImageUrl"),
                "text": top_comment.get("textDisplay"),
                "text_original": top_comment.get("textOriginal"),
                "timestamp": top_comment.get("publishedAt"),
                "like_count": top_comment.get("likeCount", 0),
            },
            "video_id": snippet.get("videoId"),
            "total_replies": snippet.get("totalReplyCount", 0),
            "replies": [
                {
                    "id": rep["id"],
                    "author": rep["snippet"]["authorDisplayName"],
                    "author_avatar": rep["snippet"]["authorProfileImageUrl"],
                    "text": rep["snippet"]["textDisplay"],
                    "timestamp": rep["snippet"]["publishedAt"]
                }
                for rep in item.get("replies", {}).get("comments", [])
            ]
        })
    return formatted

def post_reply_blocking(user_id: str, parent_id: str, text: str) -> Dict[str, Any]:
    creds = _get_creds(user_id)
    # Important: comments.insert requires full or force-ssl scope
    youtube = build("youtube", "v3", credentials=creds, cache_discovery=False)
    
    body = {
        "snippet": {
            "parentId": parent_id,
            "textOriginal": text
        }
    }
    
    res = youtube.comments().insert(
        part="snippet",
        body=body
    ).execute()
    
    return {
        "id": res["id"],
        "author": res["snippet"]["authorDisplayName"],
        "text": res["snippet"]["textOriginal"],
        "timestamp": res["snippet"]["publishedAt"]
    }

async def fetch_comments(user_id: str) -> List[Dict[str, Any]]:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, fetch_comments_blocking, user_id)

async def post_reply(user_id: str, parent_id: str, text: str) -> Dict[str, Any]:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, post_reply_blocking, user_id, parent_id, text)

# --- Delete Comment ---
def delete_comment_blocking(user_id: str, comment_id: str) -> bool:
    creds = _get_creds(user_id)
    youtube = build("youtube", "v3", credentials=creds, cache_discovery=False)
    
    try:
        # 1. Try deleting (Works if it's our own comment)
        youtube.comments().delete(id=comment_id).execute()
    except Exception as e:
        # 2. Fallback: Moderate (Reject) if it is another user's comment
        # setModerationStatus hides it from public view on the video
        try:
            youtube.comments().setModerationStatus(
                id=comment_id,
                moderationStatus='rejected'
            ).execute()
        except Exception as e2:
            print(f"[YOUTUBE DELETE FALLBACK ERROR] {e2}")
            # Re-raise the original or fallback error for debugging
            raise e
            
    return True

async def delete_comment(user_id: str, comment_id: str) -> bool:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, delete_comment_blocking, user_id, comment_id)
