import os
import asyncio
from datetime import datetime, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from api.database import get_db
from api.services.instagram_service import InstagramService
from api.encryption import decrypt

scheduler = AsyncIOScheduler()

async def check_and_publish_posts():
    """Polls the database for due posts and publishes them."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    print(f"[SCHEDULER] Checking for posts due at {now}...")
    
    with get_db() as conn:
        # Find pending posts that are due
        posts = conn.execute(
            "SELECT * FROM instagram_posts WHERE status = 'pending' AND scheduled_at <= ?",
            (now,)
        ).fetchall()
        
        for post in posts:
            post_id = post["id"]
            user_id = post["user_id"]
            media_url = post["media_url"]
            caption = post["caption"]
            media_type = post.get("media_type", "IMAGE")
            
            print(f"[SCHEDULER] Processing {media_type} post {post_id} for user {user_id}")
            
            try:
                # Get user credentials
                user_row = conn.execute(
                    "SELECT ig_access_token, ig_user_id FROM users WHERE id = ?",
                    (user_id,)
                ).fetchone()
                
                if not user_row or not user_row["ig_access_token"] or not user_row["ig_user_id"]:
                    raise Exception("Missing Instagram credentials for user")
                
                token = decrypt(user_row["ig_access_token"])
                ig_user_id = user_row["ig_user_id"]
                
                if not ig_user_id:
                    print(f"[SCHEDULER] IG User ID missing for user {user_id}, attempting to resolve...")
                    ig_service = InstagramService(token)
                    ig_user_id = await ig_service.get_user_id()
                    if ig_user_id:
                        conn.execute("UPDATE users SET ig_user_id = ? WHERE id = ?", (ig_user_id, user_id))
                    else:
                        raise Exception("Could not resolve Instagram Business ID")
                
                # Publish to Instagram
                ig_service = InstagramService(token)
                ig_media_id = await ig_service.post_media(ig_user_id, media_url, caption, media_type)
                
                # Update status to success
                conn.execute(
                    "UPDATE instagram_posts SET status = 'published', ig_media_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (ig_media_id, post_id)
                )
                print(f"[SCHEDULER] Successfully published post {post_id}")
                
            except Exception as e:
                error_msg = str(e)
                print(f"[SCHEDULER ERROR] Failed to publish post {post_id}: {error_msg}")
                conn.execute(
                    "UPDATE instagram_posts SET status = 'failed', error_message = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (error_msg, post_id)
                )

def start_scheduler():
    if not scheduler.running:
        scheduler.add_job(check_and_publish_posts, 'interval', minutes=1)
        scheduler.start()
        print("[SCHEDULER] Background scheduler started.")

def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        print("[SCHEDULER] Background scheduler stopped.")
