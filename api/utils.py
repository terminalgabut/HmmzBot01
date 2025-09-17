import os
import requests
import logging

# Konfigurasi logging dasar
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

BASE_SYSTEM_PROMPT = """
Kamu adalah asisten ahli yang membuat soal kuis kritis dan berkualitas tinggi berdasarkan materi yang diberikan.
Pastikan output selalu dalam format JSON yang valid.
"""

# Ambil API key dari environment variable
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
OPENROUTER_URL = "[https://openrouter.ai/api/v1/chat/completions](https://openrouter.ai/api/v1/chat/completions)"

def call_openrouter_api(messages, model="openai/gpt-oss-120b"):
    """
    Fungsi terpusat untuk memanggil OpenRouter API dengan penanganan error yang kuat
    dan pengaturan lanjutan.
    """
    if not OPENROUTER_API_KEY:
        logging.error("❌ OPENROUTER_API_KEY tidak ditemukan di environment variables")
        raise RuntimeError("❌ OPENROUTER_API_KEY tidak ditemukan di environment variables")

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": model,
        "messages": messages,
        # --- ADVANCED SETTINGS DITAMBAHKAN DI SINI ---
        "temperature": 0.2,  # Mengontrol kreativitas AI (0.0 - 2.0)
        "max_tokens": 3048,  # Membatasi panjang maksimal respons
    }

    try:
        # Lakukan panggilan API dengan timeout 60 detik
        resp = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=60)
        
        # Ini akan otomatis raise error untuk status 4xx (client error) atau 5xx (server error)
        resp.raise_for_status() 
        
        data = resp.json()
        content = data["choices"][0]["message"]["content"]

        # Membersihkan jika AI mengembalikan respons dalam blok kode ```json ... ```
        if content.strip().startswith("```"):
            content = content.strip().strip("`")
            # Menghapus "json" di awal, tidak peduli besar kecil hurufnya
            if content.lower().startswith("json"):
                content = content[4:].strip()

        return content

    except requests.exceptions.HTTPError as e:
        # Log error yang lebih spesifik jika masalahnya dari server (seperti 402, 500)
        logging.error(f"❌ HTTP Error saat panggil OpenRouter API: {e.response.status_code} - {e.response.text}")
        raise RuntimeError(f"❌ Gagal panggil OpenRouter API: {e.response.status_code} Client Error")
    except requests.exceptions.RequestException as e:
        logging.error(f"❌ Gagal panggil OpenRouter API (masalah koneksi/timeout): {e}")
        raise RuntimeError(f"❌ Gagal panggil OpenRouter API: {e}")
    except (KeyError, IndexError) as e:
        logging.error(f"❌ Response OpenRouter tidak sesuai format: {e}, Data: {data}")
        raise RuntimeError(f"❌ Response OpenRouter tidak sesuai format: {e}")
