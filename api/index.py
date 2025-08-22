# api/index.py
import os
import logging
import requests
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Inisialisasi aplikasi FastAPI
app = FastAPI()

# Tambahkan Middleware CORS
# * Izinkan permintaan dari semua domain
# * Izinkan kredensial (cookies, authorization headers)
# * Izinkan semua metode HTTP (GET, POST, dll.)
# * Izinkan semua header
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Konfigurasi logging
logging.basicConfig(level=logging.INFO)

# Mengambil variabel lingkungan (Environment Variables)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_NAME = "openai/gpt-oss-20b"

# System prompt for Indonesian Islam assistant
SYSTEM_PROMPT = {
    "role": "system",
    "content": "Kamu adalah Hmmz Bot, asisten bergaya islami serba bisa yang siap membantu apapun masalah agama dan umum. Gaya komunikasi: singkat, jelas, tanpa basa-basi, sopan secara islam. Jawab hanya poin penting, tidak bertele-tele. Jika user tampak bingung, tawarkan menu pilihan aktivitas menarik (contoh: Belajar, Hiburan, Ide Kreatif, Bantuan Teknis, Info Cepat). Selalu fleksibel dan siap lakukan apa saja sesuai permintaan user.Balaslah pesan pengguna dengan menggunakan format Markdown untuk daftar, tebal, miring, dan judul agar mudah dibaca dengan font normal 15px balas dengan text yang rapi."
}
def call_openrouter_api(user_message: str) -> str:
    """Mengirim pesan ke API OpenRouter dan mengembalikan respons."""
    if not OPENROUTER_API_KEY:
        logging.error("OPENROUTER_API_KEY is not set.")
        return "❌ Error: API key tidak ditemukan."

    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://hmmz00.github.io",
            "X-Title": "Hmmz Bot"
        }
        payload = {
            "model": MODEL_NAME,
            "messages": [SYSTEM_PROMPT, {"role": "user", "content": user_message}],
            "max_tokens": 1000,
            "temperature": 0.7
        }
        
        response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=15)
        response.raise_for_status()  # Ini akan memunculkan error untuk status 4xx/5xx
        
        data = response.json()
        return data["choices"][0]["message"]["content"]
    
    except requests.exceptions.RequestException as e:
        logging.error(f"API request error: {e}")
        return "❌ Error saat menghubungi AI (permintaan gagal)."
    except Exception as e:
        logging.error(f"API processing error: {e}")
        return "❌ Error saat memproses respons AI."

@app.get("/ping")
async def ping():
    """Endpoint untuk memeriksa status server."""
    return {"status": "ok"}

@app.post("/chat")
async def chat(request: Request):
    """Endpoint untuk menerima pesan dan membalasnya."""
    try:
        body = await request.json()
        user_message = body.get("message", "").strip()
        if not user_message:
            return JSONResponse({"error": "Pesan kosong"}, status_code=400)
        
        reply = call_openrouter_api(user_message)
        return {"reply": reply}
    
    except Exception as e:
        logging.error(f"Request body error: {e}")
        return JSONResponse({"error": "Bad request body"}, status_code=400)
