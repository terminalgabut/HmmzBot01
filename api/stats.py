from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from .supabase_client import supabase  

router = APIRouter()

@router.get("/stats/{user_id}", tags=["Statistics"])
async def get_user_stats(user_id: str):
    """
    Ambil riwayat kuis user dari 'kritika_attempts',
    hitung skor gabungan (akurasi + kecepatan),
    lalu kembalikan hasil akhir per dimensi untuk chart segi lima.
    """
    try:
        # 1. Query data dari Supabase
        query = (
            supabase
            .from_("kritika_attempts")
            .select("user_id, dimension, score, duration_seconds")
            .eq("user_id", user_id)
        )
        response = query.execute()

        if not response.data:
            return JSONResponse(content={})

        # 2. Hitung skor gabungan
        stats_calculator = {}
        for attempt in response.data:
            dimension = attempt.get("dimension")
            score = attempt.get("score", 0) or 0  # 0 atau 1
            duration = attempt.get("duration_seconds", 30) or 30

            # Faktor kecepatan (dibatasi 0–1)
            speed_factor = max(0, (30 - duration) / 30)

            # Skor final attempt
            final_score = score * speed_factor * 100  

            if dimension:
                if dimension not in stats_calculator:
                    stats_calculator[dimension] = {"total_score": 0.0, "count": 0}
                
                stats_calculator[dimension]["total_score"] += final_score
                stats_calculator[dimension]["count"] += 1

        # 3. Rata-rata per dimensi
        final_scores = {}
        for dimension, data in stats_calculator.items():
            avg_score = data["total_score"] / data["count"]
            final_scores[dimension] = round(avg_score)

        # 4. Return hasil bersih untuk chart segi lima
        return JSONResponse(content=final_scores)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
