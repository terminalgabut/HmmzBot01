# api/quiz.py
import os
import logging
import requests
from fastapi import APIRouter, HTTPException
from .utils import BASE_SYSTEM_PROMPT, call_openrouter_api

router = APIRouter()

@router.post("/")
async def generate_quiz(material: dict):
    try:
        messages = [
            {"role": "system", "content": BASE_SYSTEM_PROMPT},
            {"role": "user", "content": material.get("content", "")},
        ]
        result = call_openrouter_api(messages)
        return {"reply": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@router.post("/quiz")
async def generate_quiz(request: Request):
    try:
        body = await request.json()
        materi = body.get("materi", "").strip()
        session_id = body.get("session_id", "default")

        if not materi:
            return JSONResponse({"error": "Materi kosong"}, status_code=400)

        # Prompt untuk AI → wajib JSON valid
        prompt_quiz = f"""
        Buatkan 3 soal pilihan ganda berbasis teks berikut:

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
              "correct_answer": "A|B|C|D"
            }}
          ]
        }}
        - Jangan beri jawaban/kunci di luar field "correct_answer".
        - Jangan beri catatan tambahan.
        - Pastikan JSON valid.
        """

        messages = [BASE_SYSTEM_PROMPT, {"role": "user", "content": prompt_quiz}]
        ai_reply = call_openrouter_api(messages, mode="qa")

        # coba parsing JSON
        import json
        try:
            parsed = json.loads(ai_reply)
            return {"quiz": parsed, "session_id": session_id}
        except Exception as e:
            logging.error(f"JSON parse error: {e}, raw: {ai_reply}")
            return JSONResponse({"error": "AI tidak menghasilkan JSON valid", "raw": ai_reply}, status_code=500)

    except Exception as e:
        logging.error(f"Quiz error: {e}")
        return JSONResponse({"error": "Server error"}, status_code=500)
