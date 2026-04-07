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
            return JsonResponse({"error": "Lỗi đọc dữ liệu."})

        # ======================
        # 🔥 1. SAVE TRƯỚC
        # ======================
        msg = ChatMessage.objects.create(
            user=request.user,
            message=message,
            response="__thinking__"
        )

        # ======================
        # 🔥 2. BACKGROUND AI
        # ======================
        def run_ai():
            try:
                # 1. emotion
                emotion = detect_emotion(message)

                # 2. reply
                reply = generate_ai_reply(request.user, message)

                # 3. update message
                msg.response = reply
                msg.save()

                # 4. stress
                score = calculate_stress(request.user, emotion, message)

                DailyStress.objects.update_or_create(
                    user=request.user,
                    created_at=date.today(),
                    defaults={"score": score}
                )

            except Exception as e:
                print("AI THREAD ERROR:", e)
                msg.response = "Mây hơi chậm một chút, nhưng vẫn ở đây với bạn 💛"
                msg.save()

        import threading
        threading.Thread(target=run_ai, daemon=True).start()

        # ======================
        # 🔥 3. RETURN NGAY
        # ======================
        return JsonResponse({
            "status": "processing",
            "message_id": msg.id
        })

    return JsonResponse({"error": "Invalid request"})
@login_required
def chat_status(request, msg_id):
    msg = ChatMessage.objects.get(id=msg_id, user=request.user)

    return JsonResponse({
        "response": msg.response
    })