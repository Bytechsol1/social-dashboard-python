
import sqlite3
import json

db_path = 'social_intel.db'
user_id = '134acfd2-cb6e-4356-81d9-32457fc555de'

def audit():
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        print("--- Instagram Metrics Audit ---")
        cur.execute("SELECT metric_name, value, date FROM metrics WHERE user_id = ? AND source = 'instagram' ORDER BY date DESC LIMIT 20", (user_id,))
        rows = cur.fetchall()
        if not rows:
            print("No Instagram metrics found.")
        for r in rows:
            print(f"Metric: {r['metric_name']}, Value: {r['value']}, Date: {r['date']}")
            
        print("\n--- Instagram Media Audit ---")
        cur.execute("SELECT id, like_count, comments_count, timestamp FROM instagram_media WHERE user_id = ? ORDER BY timestamp DESC LIMIT 5", (user_id,))
        media = cur.fetchall()
        if not media:
            print("No Instagram media items found.")
        for m in media:
            print(f"MediaID: {m['id']}, Likes: {m['like_count']}, Comments: {m['comments_count']}, TS: {m['timestamp']}")
            
        conn.close()
    except Exception as e:
        print(f"Audit failed: {e}")

if __name__ == "__main__":
    audit()
