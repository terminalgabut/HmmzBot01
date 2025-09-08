# api/quiz.py
import os
import logging
import requests
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse  # ✅ Ditambahkan import JSONResponse
from .utils import BASE_SYSTEM_PROMPT, call_openrouter_api
import json  # ✅ Ditambahkan import json untuk parsing AI reply

router = APIRouter()

# =========================
# Endpoint utama: generate quiz
# =========================
@router.post("/quiz")
async def generate_quiz(request: Request):
    """
    Generate quiz pilihan ganda berbasis teks materi.
    Memastikan JSON valid dan jawaban benar selalu A.
    """
    try:
        body = await request.json()
        materi = body.get("materi", "").strip()
        session_id = body.get("session_id", "default")

        if not materi:
            return JSONResponse({"error": "Materi kosong"}, status_code=400)

        # Prompt untuk AI → wajib JSON valid
        prompt_quiz = f"""
        Buatkan 5 soal pilihan ganda berbasis teks berikut:

        "{materi}"

        Aturan output:
        - Kembalikan **JSON valid** tanpa tambahan teks lain.
        - Struktur JSON HARUS seperti ini:

        {{
          "questions": [
            {{
              "id": "q1",
              "question": "string",
              "options": [
                {{"key": "A", "text": "string"}},
                {{"key": "B", "text": "string"}},
                {{"key": "C", "text": "string"}},
                {{"key": "D", "text": "string"}}
              ],
              "correct_answer": "A"
            }}
          ]
        }}
        - Jawaban benar **selalu gunakan key 'A'**.
        - Jangan beri jawaban/kunci di luar field "correct_answer".
        - Jangan beri catatan tambahan.
        - Pastikan JSON valid.
        """

        # ✅ Gunakan struktur messages yang benar
        messages = [
            {"role": "system", "content": BASE_SYSTEM_PROMPT},
            {"role": "user", "content": prompt_quiz}
        ]

        # Panggil OpenRouter API
        ai_reply = call_openrouter_api(messages, mode="qa")

        # Bersihkan AI reply sebelum parsing
        ai_reply_clean = ai_reply.strip()

        try:
            parsed = json.loads(ai_reply_clean)
            return {"quiz": parsed, "session_id": session_id}
        except json.JSONDecodeError as e:
            logging.error(f"JSON parse error: {e}, raw: {ai_reply}")
            return JSONResponse(
                {"error": "AI tidak menghasilkan JSON valid", "raw": ai_reply},
                status_code=500
            )

    except Exception as e:
        logging.error(f"Quiz error: {e}")
        return JSONResponse({"error": "Server error"}, status_code=500)
