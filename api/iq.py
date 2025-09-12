from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
# Pastikan impor ini sesuai dengan struktur proyek Anda
from .supabase_client import supabase 

# --- Router Baru Khusus untuk IQ ---
router = APIRouter()

# --- Fungsi Helper ---

def get_global_stats():
    """
    Mengambil statistik rata-rata (mean) dan simpangan baku (std dev)
    dari seluruh populasi pengguna.

    NOTE: Untuk sekarang, kita gunakan data DUMMY.
    Idealnya, data ini diambil dari cache, tabel terpisah, atau dihitung secara periodik.
    """
    return {
      "Analisa": { "mean": 55, "stdDev": 15 },
      "Logika": { "mean": 60, "stdDev": 15 },
      "Pemecahan Masalah": { "mean": 65, "stdDev": 18 },
      "Konsentrasi": { "mean": 40, "stdDev": 20 },
      "Memori": { "mean": 45, "stdDev": 18 },
      # 'speed' dihitung dalam detik
      "speed": { "mean": 15, "stdDev": 5 } 
    }

def calculate_iq_score(user_scores, global_stats):
    """
    Menghitung skor IQ ekuivalen berdasarkan perbandingan skor user
    dengan statistik global menggunakan Z-Score.
    """
    z_scores = []

    for dimension, user_score in user_scores.items():
        if dimension in global_stats:
            stats = global_stats[dimension]
            mean = stats["mean"]
            std_dev = stats["stdDev"]

            if std_dev == 0: continue # Hindari pembagian dengan nol

            # Hitung Z-Score
            z = (user_score - mean) / std_dev

            # Logika khusus untuk 'speed': skor lebih rendah lebih baik,
            # jadi Z-score-nya harus kita balik (negatif jadi positif, dst.)
            if dimension == 'speed':
                z = z * -1
            
            z_scores.append(z)

    if not z_scores:
        return None

    # Rata-ratakan semua Z-Score
    avg_z_score = sum(z_scores) / len(z_scores)

    # Konversi ke skala IQ standar (Mean 100, StdDev 15) dan bulatkan
    iq_score = round(100 + (avg_z_score * 15))
    return iq_score

# --- Endpoint Baru untuk IQ ---

@router.get("/iq-score/{user_id}", tags=["IQ Calculation"])
async def get_iq_score(user_id: str):
    """
    Menghitung skor IQ ekuivalen untuk seorang pengguna.
    Endpoint ini TIDAK mengganggu endpoint /stats/{user_id} yang sudah ada.
    """
    try:
        # 1. Ambil data mentah dari Supabase
        response = supabase.from_("kritika_attempts").select(
            "dimension, score, duration_seconds"
        ).eq("user_id", user_id).execute()

        if not response.data:
            # Mengembalikan skor rata-rata jika user belum punya data
            return JSONResponse(content={"iqScore": 100, "message": "No attempts found, returning average score."})

        user_attempts = response.data

        # 2. Hitung SKOR AKURASI MURNI per dimensi (tanpa speed)
        accuracy_calculator = {}
        for attempt in user_attempts:
            dim = attempt.get("dimension")
            score = attempt.get("score", 0) or 0
            if dim:
                if dim not in accuracy_calculator:
                    accuracy_calculator[dim] = {"correct": 0, "count": 0}
                accuracy_calculator[dim]["correct"] += score
                accuracy_calculator[dim]["count"] += 1
        
        final_accuracy_scores = {
            dim: (data["correct"] / data["count"]) * 100
            for dim, data in accuracy_calculator.items()
        }

        # 3. Hitung RATA-RATA SPEED MURNI (dalam detik)
        total_duration = sum(a.get("duration_seconds", 30) for a in user_attempts)
        avg_speed = total_duration / len(user_attempts)

        # 4. Gabungkan semua skor individual milik user
        all_user_scores = {**final_accuracy_scores, "speed": avg_speed}

        # 5. Ambil statistik global (dari fungsi helper)
        global_stats = get_global_stats()

        # 6. Hitung skor IQ final
        iq_score = calculate_iq_score(all_user_scores, global_stats)
        
        if iq_score is None:
            raise HTTPException(status_code=404, detail="Could not calculate IQ score.")

        # 7. Kembalikan hasil sederhana
        return JSONResponse(content={"iqScore": iq_score})

    except Exception as e:
        # Memberikan detail error yang lebih baik untuk debugging
        print(f"Error calculating IQ for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
