import os
from supabase import create_client, Client

# Ambil URL dan Key dari environment variables untuk keamanan
# Jika Anda masih dalam tahap development, Anda bisa menaruhnya langsung di sini
# tapi JANGAN PERNAH push key Anda ke GitHub.

SUPABASE_URL = "https://jpxtbdawajjyrvqrgijd.supabase.co"
SUPABASE_KEY = "KEY_RAHASIA_ANDA"

# Inisialisasi client Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
