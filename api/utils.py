import os
import requests

BASE_SYSTEM_PROMPT = """
Kamu adalah asisten yang membuat soal kuis...
"""

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

def call_openrouter_api(messages, model="openai/gpt-oss-120b"):
    if not OPENROUTER_API_KEY:
        raise RuntimeError("❌ OPENROUTER_API_KEY tidak ditemukan di environment variables")

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": messages,
    }

    try:
        resp = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]

        # Bersihkan bila ada blok kode ```json ... ```
        if content.strip().startswith("```"):
            content = content.strip().strip("`")
            if content.lower().startswith("json"):
                content = content[4:].strip()

        return content

    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"❌ Gagal panggil OpenRouter API: {e}")
    except (KeyError, IndexError) as e:
        raise RuntimeError(f"❌ Response OpenRouter tidak sesuai format: {e}")
