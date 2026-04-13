# stress_app/views_jobs.py

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.core.management import call_command


@csrf_exempt
def run_daily_stress(request):

    key = request.GET.get("key")

    if key != settings.CRON_SECRET:
        return JsonResponse({"error": "unauthorized"}, status=403)

    call_command("daily_stress_job")

    return JsonResponse({"status": "ok"})