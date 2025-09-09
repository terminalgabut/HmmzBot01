from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
# Pastikan import ini sesuai dengan lokasi file koneksi supabase Anda
from .supabase_client import supabase  

# Membuat router baru, sama seperti yang Anda lakukan untuk kuis
router = APIRouter()

@router.get("/stats/{user_id}", tags=["Statistics"])
async def get_user_stats(user_id: str):
    """
    Mengambil data riwayat kuis seorang pengguna dari tabel 'kritika_attempts',
    menghitung skor rata-rata untuk setiap dimensi kognitif, dan
    mengembalikannya dalam format JSON yang siap untuk divisualisasikan.
    """
    try:
        # 1. Query data dari Supabase, hanya pilih kolom yang relevan
        query = supabase.from_("kritika_attempts").select("user_id, dimension, score").eq("user_id", user_id)

        response = query.execute()

        # Jika pengguna belum pernah mengerjakan kuis, kembalikan objek kosong
        if not response.data:
            return JSONResponse(content={})

        # 2. Siapkan dictionary untuk mengolah data
        stats_calculator = {}
        # Format: { "Analisa": {"total_score": 0.0, "count": 0}, ... }

        for attempt in response.data:
            dimension = attempt.get("dimension")
            # Skor default adalah 0 jika datanya tidak ada atau null
            score = attempt.get("score", 0) or 0

            if dimension:
                if dimension not in stats_calculator:
                    stats_calculator[dimension] = {"total_score": 0.0, "count": 0}
                
                stats_calculator[dimension]["total_score"] += score
                stats_calculator[dimension]["count"] += 1
        
        # 3. Hitung skor akhir dan format output
        final_scores = {}
        for dimension, data in stats_calculator.items():
            # (total skor / jumlah percobaan) dikali 100 untuk menjadi persen
            average_score = (data["total_score"] / data["count"]) * 100
            final_scores[dimension] = round(average_score) # Dibulatkan ke integer terdekat

        # 4. Kembalikan data JSON yang sudah bersih dan siap pakai
        # Contoh hasil: { "Analisa": 80, "Logika": 95, "Memori": 60 }
        return JSONResponse(content=final_scores)

    except Exception as e:
        # Menangani jika ada error tak terduga
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
      
