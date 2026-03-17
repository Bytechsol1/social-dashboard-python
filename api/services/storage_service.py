import os
import uuid
from supabase import create_client, Client

class StorageService:
    def __init__(self):
        url = os.environ.get("VITE_SUPABASE_URL")
        key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("VITE_SUPABASE_ANON_KEY")
        self.supabase: Client = create_client(url, key)
        self.bucket_name = "social-media"
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        try:
            # Check if bucket exists
            buckets = self.supabase.storage.list_buckets()
            if not any(b.name == self.bucket_name for b in buckets):
                print(f"[STORAGE] Creating bucket: {self.bucket_name}")
                self.supabase.storage.create_bucket(self.bucket_name, options={"public": True})
        except Exception as e:
            print(f"[STORAGE WARNING] Could not ensure bucket: {e}")

    async def upload_file(self, file_content: bytes, filename: str, content_type: str = "image/jpeg") -> str:
        """Uploads a file to Supabase Storage and returns a public URL."""
        # Ensure bucket exists (or at least try to use it)
        # In a real app, you'd create the bucket if it doesn't exist, 
        # but here we assume it's pre-configured or will error helpfully.
        
        file_ext = filename.split(".")[-1]
        unique_filename = f"{uuid.uuid4()}.{file_ext}"
        path = f"posts/{unique_filename}"

        # Sync upload (supabase-py is primarily sync for storage right now)
        try:
            self.supabase.storage.from_(self.bucket_name).upload(
                path=path,
                file=file_content,
                file_options={"content-type": content_type}
            )
            
            # Get public URL
            res = self.supabase.storage.from_(self.bucket_name).get_public_url(path)
            return res
        except Exception as e:
            print(f"[STORAGE ERROR] Upload failed: {e}")
            raise e
