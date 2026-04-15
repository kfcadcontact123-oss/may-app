from chat.models import ChatMessage
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import DailyStress
from django.db.models import Q, Avg
import json
from datetime import timedelta, date
import math


# =====================================
# HOME
# =====================================
@login_required
def home(request):
    request.user.refresh_from_db()
    user = request.user
    today = date.today()

    # ===== RECAP (LUÔN CÓ) =====
    yesterday = today - timedelta(days=1)

    recap_obj = DailyStress.objects.filter(
        user=user,
        created_at=yesterday
    ).first()

    # fallback nếu chưa có (KHÔNG phụ thuộc cron)
    if not recap_obj:
        class TempRecap:
            def __init__(self):
                self.score = 30
                self.ai_analysis = "Hôm qua có vẻ bạn khá yên tĩnh. Mong là bạn đang ổn theo cách của riêng mình."

        recap = TempRecap()
    else:
        recap = recap_obj

    # ===== DIFF =====
    recap_diff = None
    recap_diff_abs = None

    prev_day = yesterday - timedelta(days=1)

    prev = DailyStress.objects.filter(
        user=user,
        created_at=prev_day
    ).first()

    if prev:
        recap_diff = recap.score - prev.score
        recap_diff_abs = abs(recap_diff)

    # ===== FORECAST =====
    recent = list(
        DailyStress.objects.filter(user=user)
        .order_by("-created_at")
        .values_list("score", flat=True)[:7]
    )

    recent = list(reversed(recent))

    if len(recent) >= 2:
        forecast = predict_next_stress(recent)
        recap_forecast_text = f"{forecast}/100"
    elif len(recent) == 1:
        recap_forecast_text = "Cần thêm dữ liệu"
    else:
        recap_forecast_text = "Chưa có dữ liệu"

    # =====================================
    # 14 NGÀY
    # =====================================
    past_days = [today - timedelta(days=i) for i in range(6, -1, -1)]
    future_days = [today + timedelta(days=i) for i in range(1, 8)]

    user_records = {
        r.created_at: r.score
        for r in DailyStress.objects.filter(
            user=user,
            created_at__in=past_days
        )
    }

    global_avg = {
        d["created_at"]: d["avg"]
        for d in DailyStress.objects.filter(
            created_at__in=past_days
        ).values("created_at").annotate(avg=Avg("score"))
    }

    stress_data = []
    avg_data = []

    for d in past_days:
        stress_data.append(user_records.get(d, None))
        avg = global_avg.get(d, None)
        avg_data.append(round(avg, 1) if avg else None)

    stress_data += [None] * 7
    avg_data += [None] * 7

    # ===== TODAY =====
    stress_today = next(
        (s for s in reversed(stress_data[:7]) if s is not None),
        30
    )

    # ===== LABELS =====
    labels = [d.strftime("%d/%m") for d in (past_days + future_days)]
    start_date = past_days[0].strftime("%Y-%m-%d")

    # ===== SPECIAL CARE =====
    special_care = False
    streak = 0

    for s in reversed(stress_data[:7]):
        if s is not None and s >= 90:
            streak += 1
            if streak >= 5:
                special_care = True
                break
        else:
            break

    # ===== STATUS =====
    def get_status(score):
        if score < 30:
            return "Very Relaxed"
        elif score < 50:
            return "Relaxed"
        elif score < 70:
            return "Normal"
        elif score < 85:
            return "Stressed"
        elif score < 95:
            return "High Stress"
        else:
            return "Critical"

    status = get_status(stress_today)

    # ===== CHAT =====
    messages = ChatMessage.objects.filter(
        user=user
    ).select_related("user").order_by("created_at")

    # ===== SUGGEST USER =====
    query = request.GET.get("q", "").strip()

    base_users = User.objects.exclude(id=user.id).select_related("usermemory")

    if query:
        base_users = base_users.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query)
        )

    suggested_users = []

    if hasattr(user, "usermemory") and user.usermemory.location:
        same_location = list(
            base_users.filter(
                usermemory__location=user.usermemory.location
            )[:5]
        )

        suggested_users = same_location

        if len(suggested_users) < 5:
            remaining = list(
                base_users.exclude(
                    id__in=[u.id for u in suggested_users]
                )[:5 - len(suggested_users)]
            )
            suggested_users += remaining
    else:
        suggested_users = list(base_users[:5])

    # ===== CONTEXT =====
    context = {
        "stress_today": stress_today,
        "suggested_users": suggested_users,
        "stress_data": json.dumps(stress_data),
        "avg_data": json.dumps(avg_data),
        "start_date": start_date,
        "messages": messages,
        "status": status,
        "special_care": special_care,
        "stress_labels": json.dumps(labels),
        "query": query,

        # 🔥 recap mới
        "recap": recap,
        "recap_diff": recap_diff,
        "recap_diff_abs": recap_diff_abs,
        "recap_forecast_text": recap_forecast_text,
        "recap_date": yesterday.strftime("%Y-%m-%d"),
    }

    return render(request, "index.html", context)


# =====================================
# DONATE
# =====================================
@login_required
def donate(request):
    return render(request, "donate.html")


# =====================================
# PROFILE
# =====================================
@login_required
def profile_view(request, user_id):
    profile_user = get_object_or_404(
        User.objects.select_related("usermemory"),
        id=user_id
    )

    today = date.today()
    past_days = [today - timedelta(days=i) for i in range(6, -1, -1)]

    records = {
        r.created_at: r.score
        for r in DailyStress.objects.filter(
            user=profile_user,
            created_at__in=past_days
        )
    }

    stress_data = [records.get(d, None) for d in past_days]

    stress_today = next(
        (s for s in reversed(stress_data) if s is not None),
        30
    )

    def get_status(score):
        if score < 30:
            return "Very Relaxed"
        elif score < 50:
            return "Relaxed"
        elif score < 70:
            return "Normal"
        elif score < 85:
            return "Stressed"
        elif score < 95:
            return "High Stress"
        else:
            return "Critical"

    status = get_status(stress_today)

    context = {
        "profile_user": profile_user,
        "stress_today": stress_today,
        "status": status,
        "stress_data": json.dumps(stress_data),
        "stress_labels": json.dumps([d.strftime("%d/%m") for d in past_days]),
    }

    return render(request, "profile.html", context)


# =====================================
# PREDICT
# =====================================
def predict_next_stress(stress_list):
    if len(stress_list) < 2:
        return None

    n = len(stress_list)

    sumX = sum(range(n))
    sumY = sum(stress_list)
    sumXY = sum(i * stress_list[i] for i in range(n))
    sumXX = sum(i * i for i in range(n))

    denominator = (n * sumXX - sumX * sumX)
    if denominator == 0:
        return stress_list[-1]

    slope = (n * sumXY - sumX * sumY) / denominator

    last = stress_list[-1]
    prev = stress_list[-2]
    momentum = last - prev

    predicted = (
        last +
        slope * 0.3 +
        momentum * math.exp(-0.7) +
        (50 - last) * 0.05
    )

    return round(max(20, min(95, predicted)))


# =====================================
# DETAIL
# =====================================
@login_required
def stress_detail_view(request, date):
    from datetime import datetime

    date = datetime.strptime(date, "%Y-%m-%d").date()

    stress = DailyStress.objects.filter(
        user=request.user,
        created_at=date
    ).first()

    if not stress:
        stress = DailyStress(
            score=30,
            ai_analysis="Hôm đó bạn có vẻ khá yên tĩnh. Mong là bạn vẫn ổn."
        )

    yesterday = date - timedelta(days=1)

    yesterday_obj = DailyStress.objects.filter(
        user=request.user,
        created_at=yesterday
    ).first()

    diff = None
    diff_abs = None

    if yesterday_obj:
        diff = stress.score - yesterday_obj.score
        diff_abs = abs(diff)

    recent = list(
        DailyStress.objects.filter(user=request.user)
        .order_by("-created_at")
        .values_list("score", flat=True)[:7]
    )

    recent = list(reversed(recent))
    forecast = predict_next_stress(recent)

    if len(recent) == 0:
        forecast_text = "Chưa có dữ liệu stress nào."
    elif len(recent) == 1:
        forecast_text = "Cần ít nhất 2 ngày để dự đoán xu hướng."
    else:
        forecast_text = f"{forecast}/100"

    return render(request, "stress/detail.html", {
        "stress": stress,
        "diff": diff,
        "diff_abs": diff_abs,
        "forecast": forecast,
        "forecast_text": forecast_text
    })


# =====================================
# REDIRECT RECAP
# =====================================
def latest_recap(request):
    yesterday = date.today() - timedelta(days=1)
    return redirect(f"/stress/{yesterday}/")