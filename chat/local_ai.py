import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5:3b"

def generate_local_reply(prompt):

    full_prompt = f"""
Bạn là Mây — một người bạn tâm lý.

- trả lời dài
- có cảm xúc
- không nói ngắn

User:
{prompt}

Mây:
"""

    try:
        res = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "num_predict": 800,
                    "temperature": 0.7
                }
            },
            timeout=12
        )

        data = res.json()
        return data.get("response", "").strip()

    except Exception as e:
        print("LOCAL AI ERROR:", e)
        return "Mây đang hơi chậm một chút... bạn nói lại giúp mình nhé?"