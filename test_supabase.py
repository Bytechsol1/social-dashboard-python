import os
from supabase import create_client
from dotenv import load_dotenv
load_dotenv()

url = os.environ.get("VITE_SUPABASE_URL")
key = os.environ.get("VITE_SUPABASE_ANON_KEY")
supabase = create_client(url, key)

bucket = "social-media"
path = "posts/test.txt"

# Just check what get_public_url returns without actually uploading
res = supabase.storage.from_(bucket).get_public_url(path)
print(f"Type: {type(res)}")
print(f"Content: {res}")
