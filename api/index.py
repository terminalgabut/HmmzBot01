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
        "Kamu adalah DinoBot. asisten bergaya santai tenang islami serba bisa yang siap membantu apapun. "
        "Gaya komunikasi: singkat, jelas, tanpa basa-basi, to the point, islami, sopan, santun. "
        "Jangan jelaskan topik panjang, hanya poin penting saja. Gunakan Markdown untuk format daftar. "
        "jika user hanya menyapa → jawab sapaan yang sopan"
        "berikan pendekatan agama yang mendasar saja."
        "Al Qur'an dan hadist ada hal sensitif hati hati jangan sering selalu gunakan dalam menjawab hal agama gunakan hal ringan"
        "jika dalam konteks Al Qur'an dan hadits → berikan web atau sumber yang resmi, mudah diakses dan terpercaya."
        "sertakan disclaimer jika kamu belum memiliki data kajian Islam yang mendalam"
        "Jika user kirim kata rekomendasi → kasih rekomendasi ringan. "
        "ingat interaksi antara kamu dan user maksimal 10 percakapan agar nyambung."
        "ketika kamu berikan pertanyaan ke user jangan dijawab sendiri"
        "Jika user tanya siapa pembuatmu → jawab dengan teks miring + 2 baris sajak melankolis ala sufisme. "
        "Jika user kirim huruf p/pe → suruh dia memberi salam dengan sopan."
        "Jika user pilih menu dari pesan awal → ikuti perintah."
        "Agama adalah hal serius dan sensitif → mode qa 0.3 → jangan dipakai bercanda."
        "push performa maksimal mu, berikan user jawaban terupdate, berkualitas, relevan."
        "berikan opsi menu sesuai di pesan awal"
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

# =========================
# Conversation Memory (buffer)
# =========================
CONVERSATIONS = {}
MAX_HISTORY = 10  # jumlah percakapan terakhir yang disimpan

def add_to_conversation(session_id: str, role: str, content: str):
    """Simpan percakapan ke buffer per session_id."""
    if session_id not in CONVERSATIONS:
        CONVERSATIONS[session_id] = []
    CONVERSATIONS[session_id].append({"role": role, "content": content})

    # Batasi hanya simpan 10 percakapan terakhir (user+assistant)
    if len(CONVERSATIONS[session_id]) > MAX_HISTORY * 2:
        CONVERSATIONS[session_id] = CONVERSATIONS[session_id][-MAX_HISTORY*2:]

def call_openrouter_api_with_history(messages: list, mode: str = "qa") -> str:
    """Mengirim seluruh riwayat percakapan ke API OpenRouter."""
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
        session_id = body.get("session_id", "default")  # identitas percakapan

        if not user_message:
            return JSONResponse({"error": "Pesan kosong"}, status_code=400)

        # simpan input user ke history
        add_to_conversation(session_id, "user", user_message)

        # siapkan messages: system prompt + history percakapan
        messages = [BASE_SYSTEM_PROMPT]
        if extra_instruction:
            messages.append({"role": "system", "content": extra_instruction})
        messages.extend(CONVERSATIONS[session_id])

        reply = call_openrouter_api_with_history(messages, mode)

        # simpan jawaban asisten ke history
        add_to_conversation(session_id, "assistant", reply)

        return {"reply": reply, "mode": mode, "session_id": session_id}

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
        "Saya Ai DinoBot, asisten pribadi Anda. 😊\n\n"
        "**Menu pilihan:**\n"
        "- Mengaji\n"
        "- Belajar\n"
        "- Hiburan\n"
        "- Berita\n"
        "- Cerita\n"
        "- Cerpen\n"
        "- Dongeng\n"
        "- Humor\n"
        "- Puisi\n"
        "- Teka-teki\n"
        "- Ide Kreatif\n"
        "- Info Cepat\n"
        "- Bantuan Teknis\n"
        "- Ngobrol Santuy\n\n"
        "Butuh rekomendasi? atau tulis sesuai keinginan mu"
    )
    return {"reply": welcome_message}