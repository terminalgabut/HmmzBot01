import os
import logging
import requests
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
from dotenv import load_dotenv

# =========================
# Load env
# =========================
load_dotenv()

# Supabase setup
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# FastAPI app
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)

# =========================
# OpenRouter setup
# =========================
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_NAME = "openai/gpt-4o-mini-2024-07-18"

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

MODE_SETTINGS = {
    "qa": {"max_tokens": 800, "temperature": 0.2, "top_p": 0.6},
    "creative": {"max_tokens": 5000, "temperature": 0.9, "top_p": 0.95},
}

# =========================
# Conversation Memory
# =========================
CONVERSATIONS = {}
MAX_HISTORY = 10

def add_to_conversation(session_id: str, role: str, content: str):
    if session_id not in CONVERSATIONS:
        CONVERSATIONS[session_id] = []
    CONVERSATIONS[session_id].append({"role": role, "content": content})
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
    except Exception as e:
        logging.error(f"API error: {e}")
        return "❌ Error saat menghubungi AI."

# =========================
# API Endpoints
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
        slug = body.get("slug", "").strip()  # <= ambil slug materi

        if not user_message:
            return JSONResponse({"error": "Pesan kosong"}, status_code=400)

        # Jika ada slug → ambil materi dari Supabase
        materi_content = ""
        if slug:
            try:
                res = supabase.table("materials").select("content").eq("slug", slug).execute()
                if res.data and len(res.data) > 0:
                    materi_content = res.data[0]["content"]
            except Exception as e:
                logging.error(f"Gagal ambil materi dari Supabase: {e}")

        # simpan input user
        add_to_conversation(session_id, "user", user_message)

        # rakit messages
        messages = [BASE_SYSTEM_PROMPT]
        if extra_instruction:
            messages.append({"role": "system", "content": extra_instruction})
        if materi_content:
            messages.append({"role": "system", "content": f"Gunakan materi berikut sebagai konteks:\n{materi_content}"})
        messages.extend(CONVERSATIONS[session_id])

        reply = call_openrouter_api(messages, mode)

        add_to_conversation(session_id, "assistant", reply)
        return {"reply": reply, "mode": mode, "session_id": session_id, "materi_used": bool(materi_content)}

    except Exception as e:
        logging.error(f"Chat error: {e}")
        return JSONResponse({"error": "Bad request body"}, status_code=400)

@app.post("/check")
async def check(request: Request):
    try:
        body = await request.json()
        answer = body.get("answer", "").strip()
        materi = body.get("context", "").strip()
        session_id = body.get("session_id", "default")

        if not answer or not materi:
            return JSONResponse({"error": "Jawaban atau konteks kosong"}, status_code=400)

        last_question = ""
        if session_id in CONVERSATIONS:
            for msg in reversed(CONVERSATIONS[session_id]):
                if msg["role"] == "assistant":
                    last_question = msg["content"]
                    break
        if not last_question:
            return JSONResponse({"error": "Tidak ada pertanyaan di sesi ini."}, status_code=404)

        prompt_evaluasi = f"""
        Anda adalah seorang guru yang adil.
        
        Materi Pembelajaran: "{materi}"
        ---
        Pertanyaan: "{last_question}"
        ---
        Jawaban Siswa: "{answer}"
        ---
        Tugas:
        1. Evaluasi jawaban secara kritis.
        2. Skor 0-10 (0 bila tidak relevan).
        3. Feedback singkat, tegas, membangun.
        Format:
        Skor: [angka]
        Feedback: [teks]
        """

        messages_for_check = [BASE_SYSTEM_PROMPT, {"role": "user", "content": prompt_evaluasi}]
        evaluasi_ai = call_openrouter_api(messages_for_check)

        skor_hasil, feedback_hasil = 0, evaluasi_ai
        try:
            for line in evaluasi_ai.split('\n'):
                if "Skor:" in line:
                    skor_hasil = int(''.join(filter(str.isdigit, line)))
                if "Feedback:" in line:
                    feedback_hasil = line.split(":", 1)[1].strip()
        except Exception as e:
            logging.error(f"Parsing error: {e}")

        return {"score": skor_hasil, "feedback": feedback_hasil}
    except Exception as e:
        logging.error(f"Check error: {e}")
        return JSONResponse({"error": "Server error"}, status_code=500)

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
