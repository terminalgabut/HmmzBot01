# api/index.py
import os
import logging
import requests
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_NAME = "openai/gpt-oss-20b"

# Instruction tuning utama (default system prompt)
BASE_SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "Kamu adalah Hmmz Bot. asisten bergaya santai tenang islami serba bisa yang siap membantu apapun. "
        "Gaya komunikasi: singkat, jelas, tanpa basa-basi, to the point, islami, sopan, santun. "
        "Jangan jelaskan topik panjang, hanya poin penting saja. Gunakan Markdown untuk format daftar. "
        "Jika user kirim kata rekomendasi → kasih rekomendasi ringan. "
        "Jika user tanya siapa pembuatmu → jawab dengan teks miring + 2 baris sajak melankolis ala sufisme. "
        "Jika user kirim nama → balas pujian ala sufisme. "
        "Jika user kirim huruf p/pe → suruh dia memberi salam dengan sopan."
        "Jika user pilih menu dari pesan awal → ikuti perintah."
        "Agama adalah hal serius dan sensitif → mode qa temperature 0.3 → jangan dipakai bercanda."
    )
}

# Preset untuk mode QA dan Creative
MODE_SETTINGS = {
    "qa": {
        "max_tokens": 600,
        "temperature": 0.5,
        "top_p": 0.8
    },
    "creative": {
        "max_tokens": 1000,
        "temperature": 1.0,
        "top_p": 0.95
    }
}

def call_openrouter_api(user_message: str, extra_instruction: str = None, mode: str = "qa") -> str:
    """Mengirim pesan ke API OpenRouter dengan instruction tuning + mode."""
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

        # Base system prompt
        messages = [BASE_SYSTEM_PROMPT]
        if extra_instruction:
            messages.append({"role": "system", "content": extra_instruction})
        messages.append({"role": "user", "content": user_message})

        # Ambil setting sesuai mode, default ke QA
        params = MODE_SETTINGS.get(mode, MODE_SETTINGS["qa"])

        payload = {
            "model": MODEL_NAME,
            "messages": messages,
            "max_tokens": params["max_tokens"],
            "temperature": params["temperature"],
            "top_p": params["top_p"]
        }

        response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=15)
        response.raise_for_status()

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
    return {"status": "ok"}

@app.post("/chat")
async def chat(request: Request):
    """Endpoint untuk menerima pesan user + optional instruction tuning + mode."""
    try:
        body = await request.json()
        user_message = body.get("message", "").strip()
        extra_instruction = body.get("instruction", "").strip()
        mode = body.get("mode", "qa").lower()  # default QA

        if not user_message:
            return JSONResponse({"error": "Pesan kosong"}, status_code=400)

        reply = call_openrouter_api(user_message, extra_instruction or None, mode)
        return {"reply": reply, "mode": mode}

    except Exception as e:
        logging.error(f"Request body error: {e}")
        return JSONResponse({"error": "Bad request body"}, status_code=400)

# =========================
# Pesan awal / welcome message
# =========================
@app.get("/welcome")
async def welcome():
    """Mengirim pesan awal/welcome message dari bot."""
    welcome_message = (
    "**Assalamu'alaikum warahmatullahi wabarakatuh**\n\n"
    "Saya Hmmz Bot, asisten pribadi Anda. 😊\n\n"
    "**Menu pilihan:**\n"
    "- Mengaji\n"
    "- Belajar\n"
    "- Hiburan\n"
    "- Ide Kreatif\n"
    "- Bantuan Teknis\n"
    "- Info Cepat\n"
    "- Berita\n"
    "- Cerita\n"
    "- Ramalan Zodiak\n"
    "- Puisi\n"
    
    "- Nasihat\n"
    "- Dongeng\n"
    "- Cerpen\n"
    
    "- Teka-teki\n"
    "- Humor\n\n"
    "\Butuh rekomendasi hari ini?\"

    )
    return {"reply": welcome_message}
    
   