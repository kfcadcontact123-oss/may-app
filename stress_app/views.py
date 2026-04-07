from chat.models import ChatMessage
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import DailyStress
from chat.models import UserMemory
from django.contrib.auth.models import User
from django.db.models import Q

import json
from datetime import timedelta, date
from django.db.models import Avg


@login_required
def home(request):
    request.user.refresh_from_db()
    user = request.user
    today = date.today()

    # =====================================
    # 14 NGÀY (7 quá khứ + 7 tương lai)
    # =====================================

    past_days = [today - timedelta(days=i) for i in range(6, -1, -1)]
    future_days = [today + timedelta(days=i) for i in range(1, 8)]

    all_days = past_days + future_days

    # =====================================
    # FETCH ALL DATA 1 LẦN (TỐI ƯU)
    # =====================================

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

    # =====================================
    # BUILD DATA
    # =====================================

    stress_data = []
    avg_data = []

    for d in past_days:

        # ===== USER DATA =====
        score = user_records.get(d, None)
        stress_data.append(score)

        # ===== AVG DATA (CHỈ 7 NGÀY TRÁI) =====
        avg = global_avg.get(d, None)
        avg_data.append(round(avg, 1) if avg else None)

    # 👉 7 ngày tương lai (chỉ để chỗ trống)
    stress_data += [None] * 7
    avg_data += [None] * 7

    # =====================================
    # TODAY STRESS
    # =====================================

    stress_today = next(
        (s for s in reversed(stress_data[:7]) if s is not None),
        30
    )

    # =====================================
    # START DATE
    # =====================================

    start_date = past_days[0].strftime("%Y-%m-%d")
    labels = [
    d.strftime("%d/%m")
    for d in (past_days + future_days)
]
    # =====================================
    # SPECIAL CARE
    # =====================================

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

    # =====================================
    # STATUS
    # =====================================

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

    # =====================================
    # USER + CHAT
    # =====================================

    suggested_users = User.objects.exclude(id=user.id).select_related('usermemory')[:5]
    # =====================================
    # FRIEND STATUS MAP
    # =====================================


    for u in suggested_users:
        UserMemory.objects.get_or_create(user=u)
    messages = ChatMessage.objects.filter(
        user=user
    ).order_by("created_at")

    # =====================================
    # JSON
    # =====================================

    stress_data = json.dumps(stress_data)
    avg_data = json.dumps(avg_data)

    query = request.GET.get("q")

    suggested_users = User.objects.exclude(id=user.id).select_related('usermemory')

# 🔍 SEARCH NGAY TRÊN suggested_users
    if query:
        suggested_users = suggested_users.filter(
            Q(username__icontains=query)
    )

    suggested_users = suggested_users[:5]

# đảm bảo có UserMemory
    UserMemory.objects.bulk_create(
    [UserMemory(user=u) for u in suggested_users if not hasattr(u, "usermemory")],
    ignore_conflicts=True
)
    context = {
        "stress_today": stress_today,
        "suggested_users": suggested_users,
        "stress_data": stress_data,
        "avg_data": avg_data,
        "start_date": start_date,
        "messages": messages,
        "status": status,
        "special_care": special_care,
        "stress_labels": json.dumps(labels),
        "query": query,
    }
    return render(request, "index.html", context)
@login_required
def donate(request):
    return render(request, "donate.html")
@login_required
def profile_view(request, user_id):
    from django.shortcuts import get_object_or_404

    profile_user = get_object_or_404(User.objects.select_related("usermemory"), id=user_id)

    today = date.today()

    # =========================
    # 7 NGÀY GẦN NHẤT
    # =========================
    past_days = [today - timedelta(days=i) for i in range(6, -1, -1)]

    # fetch 1 lần
    records = {
        r.created_at: r.score
        for r in DailyStress.objects.filter(
            user=profile_user,
            created_at__in=past_days
        )
    }

    stress_data = []
    for d in past_days:
        stress_data.append(records.get(d, None))

    # =========================
    # TODAY SCORE
    # =========================
    stress_today = next(
        (s for s in reversed(stress_data) if s is not None),
        30
    )

    # =========================
    # STATUS
    # =========================
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

    # =========================
    # LABELS
    # =========================
    labels = [d.strftime("%d/%m") for d in past_days]

    # =========================
    # JSON
    # =========================
    import json
    stress_data = json.dumps(stress_data)
    labels = json.dumps(labels)

    context = {
        "profile_user": profile_user,
        "stress_today": stress_today,
        "status": status,
        "stress_data": stress_data,
        "stress_labels": labels,
    }

    return render(request, "profile.html", context)
from django.shortcuts import render, get_object_or_404
import math

def predict_next_stress(stress_list):
    """
    stress_list: list các điểm stress gần nhất (không có None)
    """

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

    # 👉 chỉ dự đoán NGÀY MAI (i = startIndex + 1)
    predicted = (
        last +
        slope * 0.3 +
        momentum * math.exp(-0.7) +
        (50 - last) * 0.05
    )

    predicted = max(20, min(95, predicted))

    return round(predicted)

@login_required
def stress_detail_view(request, date):
    from datetime import datetime

    date = datetime.strptime(date, "%Y-%m-%d").date()
    stress = get_object_or_404(
        DailyStress,
        user=request.user,
        created_at=date
    )

    # ===== hôm qua =====
    yesterday = date - timedelta(days=1)
    yesterday_obj = DailyStress.objects.filter(
        user=request.user,
        created_at=yesterday
    ).first()

    diff = None
    if yesterday_obj:
        diff = stress.score - yesterday_obj.score
        diff_abs = abs(diff)

    # ===== ngày mai (forecast từ DB) =====
    tomorrow = date + timedelta(days=1)
    # lấy 7 ngày gần nhất
    recent_stress = list(
        DailyStress.objects.filter(user=request.user)
        .order_by("-created_at")
        .values_list("score", flat=True)[:7]
    )

    recent_stress = list(reversed(recent_stress))

    forecast = predict_next_stress(recent_stress)
    if len(recent_stress) == 0:
        forecast_text = "Chưa có dữ liệu stress nào."
    elif len(recent_stress) == 1:
        forecast_text = "Cần ít nhất 2 ngày để dự đoán xu hướng."
    else:
        forecast = predict_next_stress(recent_stress)
        forecast_text = f"{forecast}/100"
    return render(request, "stress/detail.html", {
        "stress": stress,
        "diff": diff,
        "diff_abs": diff_abs,
        "forecast": forecast,
        "forecast_text":forecast_text
    })