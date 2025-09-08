import os
import logging
import json
import random
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from .utils import BASE_SYSTEM_PROMPT, call_openrouter_api

router = APIRouter()

# =========================
# Endpoint utama: generate quiz
# =========================
@router.post("/quiz")
async def generate_quiz(request: Request):
    """
    Generate quiz pilihan ganda berbasis teks materi.
    Jawaban benar dipilih secara random di backend.
    """
    try:
        body = await request.json()
        materi = body.get("materi", "").strip()
        session_id = body.get("session_id", "default")

        if not materi:
            return JSONResponse({"error": "Materi kosong"}, status_code=400)

        # Prompt untuk AI → output JSON valid
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
              "category": "jurumiya-bab1",
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
        - category tetap "jurumiya-bab1".
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
                # fallback kategori jika tidak ada
                if "category" not in q:
                    q["category"] = "jurumiya-bab1"

            return {"quiz": parsed, "session_id": session_id}

        except json.JSONDecodeError as e:
            logging.error(f"JSON parse error: {e}, raw: {ai_reply_clean}")
            return JSONResponse(
                {"error": "AI tidak menghasilkan JSON valid", "raw": ai_reply_clean},
                status_code=500
            )

    except Exception as e:
        logging.error(f"Quiz error: {e}")
        return JSONResponse({"error": "Server error", "detail": str(e)}, status_code=500)
