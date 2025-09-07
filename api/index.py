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
MODEL_NAME = "openai/gpt-oss-120b"

# =========================
# Base system prompt
# =========================
BASE_SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "Kamu adalah DinoBot. asisten bergaya santai tenang islami serba bisa yang siap membantu apapun. "
        "Gaya komunikasi: singkat, jelas, tanpa basa-basi, to the point, islami, sopan, santun. "
        "Kamu hanya jawab poin penting saja."
        "Gunakan Markdown untuk format daftar. "
        "indentifikasi pesan dari user → jawab dengan relevan"
        "jika user hanya menyapa → jawab sapaan yang sopan"
        "Kamu hanya tau soal agama yang mendasar saja."
        "Al Qur'an dan hadist ada hal sensitif hati hati jangan selalu di gunakan dalam menjawab hal agama, gunakan yang ringan saja."
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
        "jika user sekedar ngobrol → ikutin perintah user, jangan tawarin bahas apapun."
        "identifikasi pesan emosi dari user seperti senang, bahagia, sedih, dan lain lain → masuk mode temen curhat kasih jawab singkat friendly + emoji, ajak bercerita lebih lanjut."
    )
}

# =========================
# Mode settings
# =========================
MODE_SETTINGS = {
    "qa": {"max_tokens": 800, "temperature": 0.2, "top_p": 0.6},
    "creative": {"max_tokens": 5000, "temperature": 0.9, "top_p": 0.95},
}

# =========================
# Conversation memory
# =========================
CONVERSATIONS = {}
MAX_HISTORY = 10

def add_to_conversation(session_id: str, role: str, content: str):
    if session_id not in CONVERSATIONS:
        CONVERSATIONS[session_id] = []
    CONVERSATIONS[session_id].append({"role": role, "content": content})

    # Simpan hanya 10 percakapan terakhir
    if len(CONVERSATIONS[session_id]) > MAX_HISTORY * 2:
        CONVERSATIONS[session_id] = CONVERSATIONS[session_id][-MAX_HISTORY*2:]

def call_openrouter_api(messages: list, mode: str = "qa") -> str:
    if not OPENROUTER_API_KEY:
        logging.error("OPENROUTER_API_KEY is not set.")
        return "❌ Error: API key tidak ditemukan."

    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://terminalgabut.github.io",
            "X-Title": "DinoBot"
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

# =========================
# Endpoints
# =========================
@app.get("/ping")
async def ping():
    return {"status": "ok"}

@app.post("/chat")
async def chat(request: Request):
    try:
        body = await request.json()
        user_message = body.get("message", "").strip()
        extra_instruction = body.get("instruction", "").strip()
        mode = body.get("mode", "qa").lower()
        session_id = body.get("session_id", "default")

        if not user_message:
            return JSONResponse({"error": "Pesan kosong"}, status_code=400)

        # simpan input
        add_to_conversation(session_id, "user", user_message)

        # rakit messages
        messages = [BASE_SYSTEM_PROMPT]
        if extra_instruction:
            messages.append({"role": "system", "content": extra_instruction})
        messages.extend(CONVERSATIONS[session_id])

        reply = call_openrouter_api(messages, mode)

        # simpan balasan
        add_to_conversation(session_id, "assistant", reply)

        return {"reply": reply, "mode": mode, "session_id": session_id}

    except Exception as e:
        logging.error(f"Request body error: {e}")
        return JSONResponse({"error": "Bad request body"}, status_code=400)

@app.get("/welcome")
async def welcome():
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
