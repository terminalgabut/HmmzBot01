# api/index.py
import os
import logging
import requests
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

# Ganti 'default_key' dengan None untuk mencegah penggunaan kunci yang tidak valid
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_NAME = "openai/gpt-oss-20b"

# Konfigurasi logging agar lebih informatif
logging.basicConfig(level=logging.INFO)

SYSTEM_PROMPT = {
    "role": "system",
    "content": "Kamu adalah Hmmz Bot, asisten singkat, jelas, tanpa basa-basi."
}

def call_openrouter_api(user_message: str) -> str:
    # Periksa apakah API key sudah disetel
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
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except requests.exceptions.RequestException as e:
        # Menangkap error khusus dari requests
        logging.error(f"API request error: {e}")
        return "❌ Error saat menghubungi AI (request failed)."
    except Exception as e:
        # Menangkap error umum lainnya (misalnya, parsing JSON)
        logging.error(f"API processing error: {e}")
        return "❌ Error saat memproses respons AI."

@app.get("/ping")
async def ping():
    return {"status": "ok"}

@app.post("/chat")
async def chat(request: Request):
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

