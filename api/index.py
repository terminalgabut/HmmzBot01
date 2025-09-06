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

# Instruction tuning utama (default system prompt)
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

# Preset untuk mode QA dan Creative
MODE_SETTINGS = {
    "qa": {
        "max_tokens": 3000,
        "temperature": 0.2,
        "top_p": 0.9
    },
    "creative": {
        "max_tokens": 5000,
        "temperature": 0.9,
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

def call_openrouter_api(messages: list, mode: str = "qa") -> str:
    """Mengirim seluruh riwayat percakapan ke API OpenRouter."""
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

        reply = call_openrouter_api(messages, mode)

        # simpan jawaban asisten ke history
        add_to_conversation(session_id, "assistant", reply)

        return {"reply": reply, "mode": mode, "session_id": session_id}

    except Exception as e:
        logging.error(f"Request body error: {e}")
        return JSONResponse({"error": "Bad request body"}, status_code=400)

# =========================================================
# TAMBAHKAN FUNGSI BARU INI
# =========================================================
@app.post("/check")
async def check(request: Request):
    try:
        body = await request.json()
        answer = body.get("answer", "").strip()
        materi = body.get("context", "").strip()
        # Kita butuh session_id untuk tahu histori percakapannya
        session_id = body.get("session_id", "default")

        if not answer or not materi:
            return JSONResponse({"error": "Jawaban atau konteks kosong"}, status_code=400)

        # 1. Ambil pertanyaan terakhir dari histori percakapan
        last_question = ""
        if session_id in CONVERSATIONS:
            # Cari dari pesan terakhir ke belakang
            for msg in reversed(CONVERSATIONS[session_id]):
                if msg["role"] == "assistant":
                    last_question = msg["content"]
                    break
        
        if not last_question:
            return JSONResponse({"error": "Tidak ada pertanyaan yang ditemukan di sesi ini."}, status_code=404)

        # 2. Buat prompt yang detail untuk evaluasi AI
        prompt_evaluasi = f"""
        Anda adalah seorang guru yang adil dan sedang memeriksa jawaban siswa.
        
        Materi Pembelajaran: "{materi}"
        ---
        Pertanyaan yang Diajukan: "{last_question}"
        ---
        Jawaban Siswa: "{answer}"
        ---
        Tugas Anda:
        1. Evaluasi jawaban secara kritis berdasarkan relevansinya dengan materi dan pertanyaan.
        2. Berikan skor numerik antara 0 hingga 10. jawaban tidak relevan skor 0.
        3. Berikan feedback yang tegas, jelas, singkat, dan membangun.
        4. PENTING: Kembalikan jawaban Anda HANYA dalam format berikut, tanpa penjelasan tambahan:
        Skor: [skor Anda di sini]
        Feedback: [feedback Anda di sini]
        """
        
        # 3. Panggil API AI untuk evaluasi (menggunakan base prompt sistem)
        messages_for_check = [BASE_SYSTEM_PROMPT, {"role": "user", "content": prompt_evaluasi}]
        evaluasi_ai = call_openrouter_api(messages_for_check)

        # 4. Parse skor dan feedback dari respons AI
        skor_hasil = 0
        feedback_hasil = "Gagal memproses feedback dari AI. Respons mentah: " + evaluasi_ai

        try:
            # Cari baris yang mengandung "Skor:" dan "Feedback:"
            for line in evaluasi_ai.split('\n'):
                if "Skor:" in line:
                    # Ambil angka dari baris "Skor: 85"
                    skor_hasil = int(''.join(filter(str.isdigit, line)))
                if "Feedback:" in line:
                    # Ambil teks setelah kata "Feedback: "
                    feedback_hasil = line.split(":", 1)[1].strip()
        except Exception as e:
            print(f"Error saat parsing respons AI: {e}")
            # Jika gagal parsing, tampilkan saja seluruh respons AI sebagai feedback
            feedback_hasil = evaluasi_ai

        return {"score": skor_hasil, "feedback": feedback_hasil}

    except Exception as e:
        print(f"Error di endpoint /check: {e}")
        return JSONResponse({"error": "Terjadi kesalahan di server"}, status_code=500)

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
