import json
from datetime import date

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

from .ai_service import generate_ai_reply
from .models import ChatMessage
from .services.ai_emotion import detect_emotion

from stress_app.models import DailyStress
from stress_app.stress_engine import calculate_stress


@login_required
def chat_api(request):

    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
            message = data.get("message", "")
        except Exception:
            return JsonResponse({"reply": "Lỗi đọc dữ liệu."})

        # ======================
        # 1. DETECT EMOTION (AI)
        # ======================
        emotion = detect_emotion(message)

        # ======================
        # 2. AI REPLY
        # ======================
        reply = generate_ai_reply(request.user, message)

        # ======================
        # 3. 🔥 SAVE CHAT TRƯỚC (QUAN TRỌNG NHẤT)
        # ======================
        ChatMessage.objects.create(
            user=request.user,
            message=message,
            response=reply
        )

        # ======================
        # 4. 🔥 UPDATE STRESS (SAU KHI ĐÃ CÓ MESSAGE)
        # ======================
        score = calculate_stress(request.user, emotion, message)

        DailyStress.objects.update_or_create(
            user=request.user,
            created_at=date.today(),
            defaults={"score": score}
        )

        # ======================
        # RESPONSE
        # ======================
        return JsonResponse({"reply": reply})

    return JsonResponse({"reply": "Invalid request"})