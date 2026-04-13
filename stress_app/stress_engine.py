from chat.models import ChatMessage
from datetime import date, timedelta
from accounts.services.notification_service import notify_stress
from accounts.models_notification import Notification
import json
import os
from django.utils import timezone
from google.cloud import aiplatform
from web_project.settings import GOOGLE_CLOUD_PROJECT
from chat.services.ai_emotion import init_vertex
from vertexai.generative_models import GenerativeModel


# =====================
# DEBUG FLAG
# =====================
DEBUG_STRESS = True
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
def dprint(title, data=None):
    if not DEBUG_STRESS:
        return
    print(f"\n===== {title} =====")
    if isinstance(data, dict):
        for k, v in data.items():
            print(f"{k}: {v}")
    elif data is not None:
        print(data)



# =====================
# AI ANALYSIS
# =====================
def analyze_message_context(msg):
    init_vertex()

    # 🔥 ADD DÒNG NÀY
    model = GenerativeModel("gemini-2.5-flash")
    """
    FULL AI: emotion + scores
    """

    if not msg or not msg.strip():
        return {
            "emotion": "neutral",
            "scores": {
                "sad": 0.0,
                "anxiety": 0.0,
                "anger": 0.0,
                "joy": 0.0,
                "self_hate": 0.0,
                "critical": 0.0,
                "profanity": 0.0
            }
        }

    prompt = f"""
Bạn là hệ thống phân tích tâm lý.

Phân tích câu:
"{msg}"

Trả về JSON DUY NHẤT:

{{
  "emotion": "neutral | stress | sad | very_sad | critical",
  "scores": {{
    "sad": 0-1,
    "anxiety": 0-1,
    "anger": 0-1,
    "joy": 0-1,
    "self_hate": 0-1,
    "critical": 0-1,
    "profanity": 0-1
  }}
}}

Không giải thích.
"""

    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        dprint("RAW GEMINI RESPONSE", text)

        start = text.find("{")
        end = text.rfind("}") + 1
        json_str = text[start:end]

        data = json.loads(json_str)

        dprint("AI RAW", text)
        dprint("AI PARSED", data)

        return {
            "emotion": data.get("emotion", "neutral"),
            "scores": {
                "sad": float(data.get("scores", {}).get("sad", 0)),
                "anxiety": float(data.get("scores", {}).get("anxiety", 0)),
                "anger": float(data.get("scores", {}).get("anger", 0)),
                "joy": float(data.get("scores", {}).get("joy", 0)),
                "self_hate": float(data.get("scores", {}).get("self_hate", 0)),
                "critical": float(data.get("scores", {}).get("critical", 0)),
                "profanity": float(data.get("scores", {}).get("profanity", 0)),
            }
        }

    except Exception as e:
        dprint("AI ERROR", str(e))

        return {
            "emotion": "stress",
            "scores": {
                "sad": 0.3,
                "anxiety": 0.3,
                "anger": 0.1,
                "joy": 0.1,
                "self_hate": 0.0,
                "critical": 0.0,
                "profanity": 0.0
            }
        }


# =====================
# CLAMP
# =====================
def clamp(x, a, b):
    return max(a, min(x, b))


# =====================
# MAIN FUNCTION
# =====================
def calculate_stress(user, emotion, current_message=None):

    today = date.today()

    # =====================
    # 1. BASE
    # =====================
    base_map = {
        "neutral": 20,
        "stress": 45,
        "sad": 55,
        "very_sad": 70,
        "critical": 90,
    }
    now = timezone.now()
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    today_msgs_qs = ChatMessage.objects.filter(
        user=user,
        created_at__gte=start
)

    today_msgs = list(today_msgs_qs.values_list("message", flat=True))
    msg_count = len(today_msgs)

    dprint("TODAY MSGS", {
        "count": msg_count,
        "last_msgs": today_msgs[-3:]
    })

    # =====================
    # 3. FREQUENCY
    # =====================
    frequency_bonus = min(msg_count * 1.5, 15)

    # =====================
    # 4. TREND
    # =====================
    week_ago = today - timedelta(days=7)

    weekly_msgs = ChatMessage.objects.filter(
        user=user,
        created_at__date__gte=week_ago
    ).count()

    trend_bonus = min(weekly_msgs // 4, 12)

    # =====================
    # 🔥 5. AI SCORING (FIX CHUẨN)
    # =====================
    context_msgs = today_msgs[-2:]  # lấy 2 msg gần nhất

    # 🔥 thêm message hiện tại vào (QUAN TRỌNG)
    if current_message:
        context_msgs.append(current_message)

    context_msg = " ".join(context_msgs)

    ai_data = analyze_message_context(context_msg)

    # 🔥 TÁCH ĐÚNG STRUCTURE
    ai = ai_data["scores"]
    ai_emotion = ai_data["emotion"]
    # =====================
    # 🔥 FIX EMOTION LOGIC (QUAN TRỌNG NHẤT)
    # =====================
    # Ưu tiên scores hơn label của AI

    if ai["joy"] > 0.7 and ai["sad"] < 0.2 and ai["critical"] < 0.5:
        ai_emotion = "neutral"

    elif ai["critical"] > 0.8 or ai["self_hate"] > 0.7:
        ai_emotion = "critical"

    elif ai["sad"] > 0.7:
        ai_emotion = "very_sad"

    elif ai["sad"] > 0.4 or ai["anxiety"] > 0.5:
        ai_emotion = "sad"

    elif ai["anxiety"] > 0.4:
        ai_emotion = "stress"
    emotion = ai_emotion
    dprint("COMPARE EMOTION", {
    "input": emotion,
    "ai": ai_emotion
})
    dprint("AI EMOTION", ai_emotion)
    dprint("AI SCORES", ai)

        # =====================
    # 🔥 6. MAP → SCORE (FIX SIGN + SCALE)
    # =====================

    base = base_map.get(emotion, 20)

    # NEGATIVE (tăng stress)
    negative_score = (
        ai["sad"] * 28 +
        ai["anxiety"] * 24 +
        ai["anger"] * 14 +
        ai["critical"] * 40 +
        ai["self_hate"] * 32
    )

    # POSITIVE (GIẢM stress - FIX CRITICAL BUG)
    positive_offset = ai["joy"] * 35

    message_stress = base + negative_score - positive_offset
    message_stress = clamp(message_stress, 0, 100)


    # =====================
    # 7. INERTIA (GIỮ NGUYÊN LOGIC, CHỈ GIẢM SCALE)
    # =====================

    yesterday = today - timedelta(days=1)

    yesterday_msgs = ChatMessage.objects.filter(
        user=user,
        created_at__date=yesterday
    ).count()

    inertia_bonus = min(yesterday_msgs * 1.5, 8)


    # =====================
    # 8. NORMALIZE INPUT (ĐƯA VỀ 0–100)
    # =====================

    frequency_n = clamp(frequency_bonus * 8, 0, 100)
    trend_n = clamp(trend_bonus * 10, 0, 100)
    inertia_n = clamp(inertia_bonus * 10, 0, 100)
    message_n = message_stress  # đã clamp


    # =====================
    # 9. WEIGHTED COMBINE (SUM = 1)
    # =====================

    W_MESSAGE = 0.6
    W_FREQ    = 0.15
    W_TREND   = 0.15
    W_INERTIA = 0.10

    stress_score = (
        message_n * W_MESSAGE +
        frequency_n * W_FREQ +
        trend_n * W_TREND +
        inertia_n * W_INERTIA
    )


    # =====================
    # 10. SMOOTH HISTORY (SUM = 1)
    # =====================

    history_factor = clamp(msg_count / 10, 0, 1)

    stress_score = (
        stress_score * history_factor +
        base * (1 - history_factor)
    )


    # =====================
    # 11. HARD RULE (GIỮ NHẸ)
    # =====================

    if ai["critical"] > 0.85:
        stress_score = max(stress_score, 75)

    # ❗ FIX QUAN TRỌNG: vui thì phải thấp
    if ai["joy"] > 0.75 and ai["sad"] < 0.2:
        stress_score = min(stress_score, 40)


    # =====================
    # FINAL
    # =====================

    final_score = int(clamp(stress_score, 0, 100))
    return final_score