# api/quiz.py
import logging
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

# Import fungsi dari index.py
from index import call_openrouter_api

router = APIRouter()

# =========================
# Endpoint: generate quiz
# =========================
@router.post("/quiz/generate")
async def generate_quiz(request: Request):
    try:
        body = await request.json()
        materi_content = body.get("materi", "").strip()
        jumlah = body.get("jumlah", 3)

        if not materi_content:
            return JSONResponse({"error": "Materi kosong"}, status_code=400)

        messages = [
            {
                "role": "system",
                "content": (
                    "Kamu adalah generator soal yang ahli dan profesional. "
                    "Buat soal pilihan ganda harus dari materi berikut. "
                    "Format jawaban HARUS JSON valid tanpa teks tambahan. "
                    "Jangan tampilkan kunci jawaban dalam output."
                    "Contoh:\n"
                    "{\n"
                    '  \"questions\": [\n'
                    '    {\"id\": 1, \"question\": \"Apa ...?\", \"options\": [\"A\", \"B\", \"C\", \"D\"]}\n'
                    "  ]\n"
                    "}"
                )
            },
            {"role": "user", "content": f"Buat {jumlah} soal dari materi ini:\n{materi_content}"}
        ]

        reply = call_openrouter_api(messages)
        if not reply:
            return JSONResponse({"error": "Gagal generate soal"}, status_code=500)

        return {"quiz": reply}

    except Exception as e:
        logging.error(f"Generate quiz error: {e}")
        return JSONResponse({"error": "Bad request"}, status_code=400)

# =========================
# Endpoint: check answer
# =========================
@router.post("/quiz/check")
async def check_quiz(request: Request):
    try:
        body = await request.json()
        user_answers = body.get("answers", {})

        if not user_answers:
            return JSONResponse({"error": "Jawaban kosong"}, status_code=400)

        # Simpel: serahkan ke AI untuk koreksi
        messages = [
            {
                "role": "system",
                "content": (
                    "Kamu adalah pemeriksa jawaban. "
                    "Input berupa jawaban user dan soal asli. "
                    "Keluarkan hasil dalam JSON valid:\n"
                    "{ \"score\": X, \"feedback\": \"...\" }"
                )
            },
            {"role": "user", "content": f"Periksa jawaban berikut:\n{user_answers}"}
        ]

        reply = call_openrouter_api(messages)
        if not reply:
            return JSONResponse({"error": "Gagal koreksi jawaban"}, status_code=500)

        return {"result": reply}

    except Exception as e:
        logging.error(f"Check quiz error: {e}")
        return JSONResponse({"error": "Bad request"}, status_code=400)
