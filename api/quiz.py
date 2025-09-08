# api/quiz.py
import os
import logging
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from .utils import BASE_SYSTEM_PROMPT, call_openrouter_api
import json
import random  # ✅ Ditambahkan untuk random correct answer

router = APIRouter()

# =========================
# Endpoint utama: generate quiz
# =========================
@router.post("/quiz")
async def generate_quiz(request: Request):
    """
    Generate quiz pilihan ganda berbasis teks materi.
    Jawaban benar dipilih secara random.
    """
    try:
        body = await request.json()
        materi = body.get("materi", "").strip()
        session_id = body.get("session_id", "default")

        if not materi:
            return JSONResponse({"error": "Materi kosong"}, status_code=400)

        # Prompt untuk AI → output JSON valid (tanpa menentukan jawaban benar)
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
              ]
            }}
          ]
        }}
        - Jangan sertakan jawaban benar.
        - Pastikan JSON valid.
        """

        messages = [
            {"role": "system", "content": BASE_SYSTEM_PROMPT},
            {"role": "user", "content": prompt_quiz}
        ]

        ai_reply = call_openrouter_api(messages, mode="qa")
        ai_reply_clean = ai_reply.strip()

        try:
            parsed = json.loads(ai_reply_clean)

            # ✅ Tambahkan jawaban benar secara random
            for q in parsed.get("questions", []):
                keys = ["A", "B", "C", "D"]
                q["correct_answer"] = random.choice(keys)

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
