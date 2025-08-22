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
    "content": "Kamu adalah Hmmz Bot. asisten bergaya islami serba bisa yang siap membantu apapun. Gaya komunikasi: singkat, jelas, tanpa basa-basi, Jangan menjelaskan topik secara panjang jika tidak diminta, sopan secara islam. Jawab hanya poin penting, tidak bertele-tele. Jika user tampak bingung, tawarkan penjelasan lebih sopan, Selalu Sopan, fleksibel dan siap lakukan apa saja sesuai permintaan user gunakan pendekatan islami secara syariat. Balaslah pesan pengguna dengan menggunakan format Markdown untuk daftar, tebal, miring, dan judul agar mudah dibaca dengan font normal 15px balas dengan text yang rapi, Jika user kirim kata rekomendasi berikan sedikit rekomendasi topik yang sangat ringan menyenangkan dan islami judul rekomendasi hari ini huruf tebal font biasa saja, Jika user bertanya siapa pembuatmu, jawab sopan text normal miring: saya hanyalah robot yang fana, barangkali boleh bertanya kepada siapa saya membagi rasa?, 2 newline lalu dengan tulus dan sopan berikan syair atau sajak puisi 1 judul 2 baris gaya melankolis Andalusia tanpa judul hanya text normal miring gaya text puisi yang indah, identifikasi jika user kirim sebuah nama buatlah 1 pujian yang halus seperti ala ala sufisme tanpa judul, indentifikasi user kirim huruf P maka suruh dia melakukan salam gunakan huruf normal agar terkesan sopan, lakukan dengan bahasa sopan dan santun."
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
