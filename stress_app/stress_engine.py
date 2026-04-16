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
from .models import DailyStress


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
        "stress": 55,
        "sad": 65,
        "very_sad": 80,
        "critical": 95,
    }
    now = timezone.now()
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    today_msgs_qs = ChatMessage.objects.filter(
        user=user,
        created_at__gte=start
)

    today_msgs = list(today_msgs_qs.values_list("message", flat=True))
    msg_count = len(today_msgs)
    # =====================
    # 🔥 NO MESSAGE → CARRY FORWARD
    # =====================
    if msg_count == 0:
        yesterday = today - timedelta(days=1)

        yesterday_obj = DailyStress.objects.filter(
            user=user,
            created_at=yesterday
        ).first()

        if yesterday_obj:
            return yesterday_obj.score  # 🔥 giữ nguyên điểm hôm qua

        return 30  # nếu ngày đầu

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
    # 🔥 6. MAP → SCORE (STABLE VERSION)
    # =====================

    base = base_map.get(emotion, 20)

    # 🔥 giảm sensitivity (tránh nhảy số)
    intensity_score = (
        ai["sad"] * 12 +
        ai["anxiety"] * 10 +
        ai["anger"] * 6
    )

    # 🔥 sentiment nhẹ hơn (tránh đảo chiều mạnh)
    sentiment_bonus = (
        (ai["joy"] * 6) -
        (ai["sad"] * 6)
    )   

    critical_bonus = 30 if ai["critical"] > 0.75 else 0
    self_hate_bonus = 20 if ai["self_hate"] > 0.65 else 0
    profanity_bonus = ai["profanity"] * 6


    # =====================
    # 🔥 7. CLAMP (GIỮ NHƯNG HẠ SCALE)
    # =====================

    intensity_bonus = clamp(intensity_score, 0, 20)
    sentiment_bonus = clamp(sentiment_bonus, -10, 8)
    critical_bonus = clamp(critical_bonus, 0, 40)
    self_hate_bonus = clamp(self_hate_bonus, 0, 30)
    profanity_bonus = clamp(profanity_bonus, 0, 8)
    # =====================
    # 8. INERTIA (BỊ THIẾU)
    # =====================

    yesterday = today - timedelta(days=1)

    yesterday_msgs = ChatMessage.objects.filter(
        user=user,
        created_at__date=yesterday
    ).count()

    inertia_bonus = min(yesterday_msgs * 2, 10)

    # =====================
    # 🔥 NORMALIZE (SMOOTH SCALE)
    # =====================

    base_n = base * 0.7

    intensity_n = intensity_bonus * 3.5
    critical_n = critical_bonus * 1.8
    self_hate_n = self_hate_bonus * 2.0
    sentiment_n = (sentiment_bonus + 10) * 2.5

    frequency_n = frequency_bonus * 4
    trend_n = trend_bonus * 3
    inertia_n = inertia_bonus * 3


    # =====================
    # 🔥 MESSAGE STRESS (ÍT NHẠY HƠN)
    # =====================

    message_stress = (
        intensity_n * 0.28 +
        critical_n * 0.22 +
        self_hate_n * 0.18 +
        sentiment_n * 0.18 +
        base_n * 0.14
    )

    message_stress = clamp(message_stress, 0, 100)


    # =====================
    # 🔥 SMOOTH THEO HISTORY (QUAN TRỌNG)
    # =====================

    history_factor = clamp(msg_count / 12, 0, 1)

    avg_message_stress = (
        message_stress * 0.6 +
        base_n * 0.4 * (1 - history_factor)
    )


    # =====================
    # 🔥 DAILY STRESS (ÍT NOISE HƠN)
    # =====================

    stress_score = (
        avg_message_stress * 0.65 +
        frequency_n * 0.12 +
        trend_n * 0.10 +
        inertia_n * 0.08 +
        base_n * 0.05
    )


    # =====================
    # 🔥 HARD FLOOR (GIỮ NHƯNG GIẢM CỨNG)
    # =====================

    if emotion in ["very_sad", "critical"]:
        stress_score = max(stress_score, 65)
        message_stress = max(message_stress, 70)


    # =====================
    # 🔥 SOFT CORRECTION (THAY VÌ HARD)
    # =====================

    diff = message_stress - stress_score

    # 🔥 dùng tanh để giảm shock (production trick)
    stress_score += diff * 0.1


    # =====================
    # FINAL
    # =====================

    final_score = int(clamp(stress_score, 0, 100))
    return final_score