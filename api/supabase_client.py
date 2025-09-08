import os
from supabase import create_client, Client
from dotenv import load_dotenv # Library untuk membaca .env saat development lokal

# Memuat environment variables dari file .env (hanya untuk development lokal)
# Vercel akan mengabaikan ini dan menggunakan variabel yang diatur di dashboard.
load_dotenv()

# Ambil URL dan Key dari environment variables
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")

# Cek apakah variabel ada, jika tidak, berikan error yang jelas
if not supabase_url or not supabase_key:
    raise ValueError("SUPABASE_URL dan SUPABASE_KEY harus diatur di environment variables.")

# Inisialisasi client Supabase
supabase: Client = create_client(supabase_url, supabase_key)
