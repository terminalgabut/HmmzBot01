import os
from supabase import create_client, Client
from dotenv import load_dotenv # Library untuk membaca .env saat development lokal

# Memuat environment variables dari file .env (hanya untuk development lokal)
# Vercel akan mengabaikan ini dan menggunakan variabel yang diatur di dashboard.

# Ambil URL dan Key dari environment variables
supabase_url = "https://jpxtbdawajjyrvqrgijd.supabase.co"
supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpweHRiZGF3YWpqeXJ2cXJnaWpkIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NjMxMjg5OCwiZXhwIjoyMDcxODg4ODk4fQ.1-CFqhW0mXPyv8jFyd-sa4m2FoCkyY4LbgiKGIKwb6I"

# Cek apakah variabel ada, jika tidak, berikan error yang jelas

# Inisialisasi client Supabase
supabase: Client = create_client(supabase_url, supabase_key)
