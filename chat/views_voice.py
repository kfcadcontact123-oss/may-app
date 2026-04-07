from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from chat.services.voice_service import synthesize_voice, get_cache_path
from chat.models import VoiceUsage


MAX_VOICE_PER_DAY = 10


@require_GET
@login_required
def get_voice(request):

    text = request.GET.get("text")

    if not text:
        return JsonResponse({"error": "Missing text"}, status=400)

    today = timezone.now().date()

    # =========================
    # 🔥 CHECK CACHE TRƯỚC
    # =========================
    cache_path = get_cache_path(text)

    is_cached = False
    try:
        import os
        is_cached = os.path.exists(cache_path)
    except:
        pass

    # =========================
    # 🔥 LẤY / TẠO USAGE
    # =========================
    usage, _ = VoiceUsage.objects.get_or_create(
        user=request.user,
        date=today
    )

    # =========================
    # 🔥 NẾU CHƯA CACHE → CHECK LIMIT
    # =========================
    if not is_cached:
        if usage.count >= MAX_VOICE_PER_DAY:
            return JsonResponse({
                "error": "Bạn đã dùng hết 10 lượt voice hôm nay rồi 🥺"
            }, status=403)

        # 👉 tăng count
        usage.count += 1
        usage.save()

    # =========================
    # 🔥 GENERATE / LOAD AUDIO
    # =========================
    audio = synthesize_voice(text)

    response = HttpResponse(audio, content_type="audio/mpeg")
    response["Accept-Ranges"] = "bytes"
    response["Content-Length"] = len(audio)

    return response
import os

@login_required
def check_voice_exists(request):
    text = request.GET.get("text")

    if not text:
        return JsonResponse({"exists": False})

    path = get_cache_path(text)

    return JsonResponse({
        "exists": os.path.exists(path)
    })