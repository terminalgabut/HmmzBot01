# api/utils.py

BASE_SYSTEM_PROMPT = """
Kamu adalah asisten yang membuat soal kuis...
"""

import os, requests

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

def call_openrouter_api(messages, model="gpt-4o-mini"):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": messages,
    }
    resp = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]
