import logging
import json
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from .utils import BASE_SYSTEM_PROMPT, call_openrouter_api

router = APIRouter()

@router.post("/quiz")
async def generate_quiz(request: Request):
    """
    Generate quiz pilihan ganda berbasis teks materi.
    Jawaban benar disimpan sebagai teks, bukan A/B/C/D.
    """
    try:
        body = await request.json()
        materi = body.get("materi", "").strip()
        session_id = body.get("session_id", "default")

        if not materi:
            return JSONResponse({"error": "Materi kosong"}, status_code=400)

        prompt_quiz = f"""
        Buatkan 5 soal pilihan ganda berbasis teks berikut:

                           "{materi}"

        Aturan output:
        - Setiap soal fokus ke satu dimensi kognitif berikut: 
          1. Analisa
          2. Logika
          3. Pemecahan Masalah
          4. Konsentrasi
          5. Memori
        - Kembalikan **JSON valid** tanpa tambahan teks lain.
        - Struktur JSON HARUS seperti ini:

    {{
      "questions": [
    {{
      "id": "q1",
      "category": "jurumiya-bab1",
      "dimension": "Analisa",
      "question": "string",
      "options": [
        {{"text": "string"}},
        {{"text": "string"}},
        {{"text": "string"}},
        {{"text": "string"}}
      ],
      "answer": "teks yang persis salah satu dari options"
        }}
        ]
        }}

        - Jangan sertakan huruf A/B/C/D di opsi.
        - Pastikan JSON valid.
        - category tetap "jurumiya-bab1".
        - jawaban benar harus jelas sesuai salah satu opsi.
        - buat soal menantang dan relevan dengan materi.
        """

        messages = [
            {"role": "system", "content": BASE_SYSTEM_PROMPT},
            {"role": "user", "content": prompt_quiz}
        ]

        ai_reply = call_openrouter_api(messages).strip()

        try:
            parsed = json.loads(ai_reply)

            for q in parsed.get("questions", []):
                # flatten options jadi list string
                q["options"] = [opt["text"] for opt in q["options"]]
                # simpan jawaban benar sebagai teks
                q["correct_answer"] = q.get("answer")
                q.pop("answer", None)
                if not q.get("category"):
                    q["category"] = "jurumiya-bab1"

            return {"quiz": parsed, "session_id": session_id}

        except json.JSONDecodeError as e:
            logging.error(f"JSON parse error: {e}, raw: {ai_reply[:200]}")
            return JSONResponse(
                {"error": "AI tidak menghasilkan JSON valid", "raw": ai_reply},
                status_code=500
            )

    except Exception as e:
        logging.error(f"Quiz error: {e}")
        return JSONResponse({"error": "Server error", "detail": str(e)}, status_code=500)
