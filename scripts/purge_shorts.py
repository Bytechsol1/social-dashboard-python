from api.database import get_db

def purge():
    with get_db() as conn:
        conn.execute("DELETE FROM youtube_videos")
        print("Purged old cached videos lists successfully!")

if __name__ == "__main__":
    purge()
