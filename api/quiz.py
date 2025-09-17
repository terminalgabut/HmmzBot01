import logging
import json
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
# Pastikan Anda mengimpor fungsi ini dengan benar dari lokasi file utilitas Anda
from .utils import BASE_SYSTEM_PROMPT, call_openrouter_api

router = APIRouter()

@router.post("/quiz")
async def generate_quiz(request: Request):
    """
    Generate 5 soal kritis memuat analisa, logika, pemecahan masalah, konsentrasi, dan memori pilihan ganda berbasis teks materi.
    Jawaban benar dicatat sebagai teks yang persis sama dengan salah satu opsi,
    bukan sebagai huruf A/B/C/D.
    """
    try:
        body = await request.json()
        materi = body.get("materi", "").strip()
        session_id = body.get("session_id", "default")

        if not materi:
            return JSONResponse({"error": "Materi kosong"}, status_code=400)

        prompt_quiz = f"""
Buatkan 5 soal test iq pilihan ganda berbasis teks berikut:

             {materi}

Aturan output:
1. Setiap 1 soal HARUS FOKUS pada satu dimensi kognitif berikut (urutan boleh acak):
   - Analisa
   - Logika
   - Pemecahan Masalah
   - Konsentrasi
   - Memori
2. Kembalikan **HANYA JSON valid** tanpa teks apapun di luar JSON.
3. Struktur JSON HARUS seperti ini:

{{
  "questions": [
    {{
      "id": "q1",
      "category": "nahwu-bab1",
      "dimension": "Analisa",
      "question": "soal kritis bervariasi dan jelas sesuai materi",
      "options": ["opsi1", "opsi2", "opsi3", "opsi4"],
      "correct_answer": "teks yang persis salah satu dari options"
    }}
  ]
}}

4. Jangan sertakan huruf A/B/C/D di opsi.
5. Jangan tambahkan penjelasan, catatan, atau teks lain di luar JSON.
6. Pastikan jawaban benar selalu sesuai salah satu opsi.
7. SETIAP SOAL HARUS MENANTANG dan kritis gunakan beberapa variasi soal: kecuali, yang bukan, soal cerita yang sesuai dengan materi.
8. Gunakan tanda kutip yang benar dan hindari karakter escape yang rusak agar JSON valid.
9. Variasikan dimensi setiap soal sehingga kelima dimensi tercakup.
10. Nomor soal (`id`) harus otomatis urut q1..q5.
11. Untuk user demo/guest, user_id boleh null; tidak perlu menyimpan attempt.
"""

# ======================================================================
# HAPUS print(prompt_quiz) YANG LAMA
# GANTI DENGAN LOGGING YANG LEBIH BAIK SEPERTI INI:
# ======================================================================
logging.info(f"Menerima permintaan kuis.")
logging.info(f"Panjang materi: {len(materi)} karakter.")
logging.info(f"Potongan awal materi: {materi[:10]}...") # Hanya tampilkan 100 karakter pertama
# ======================================================================

messages = [
    {"role": "system", "content": BASE_SYSTEM_PROMPT},
    {"role": "user", "content": prompt_quiz}
]

        ai_reply = call_openrouter_api(messages).strip()

        try:
            parsed = json.loads(ai_reply)

            for q in parsed.get("questions", []):
                # Menangani jika AI keliru menggunakan key "answer"
                if "answer" in q and "correct_answer" not in q:
                    q["correct_answer"] = q.pop("answer")
                
                # Set default category jika tidak ada
                if not q.get("category"):
                    q["category"] = "nahwu-bab1"

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
