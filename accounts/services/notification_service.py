from accounts.models_notification import Notification
from datetime import date

# =========================
# CORE
# =========================
def create_notification(user, content, type="info", target_url=None):
    return Notification.objects.create(
        user=user,
        content=content,
        type=type,
        target_url=target_url,
    )

# =========================
# STRESS (ANTI SPAM)
# =========================
def notify_stress(user, score):

    today = date.today()

    # ❌ nếu hôm nay đã có rồi → không tạo nữa
    exists = Notification.objects.filter(
        user=user,
        type="stress",
        created_at__date=today
    ).exists()

    if exists:
        return

    # ✅ tạo 1 lần/ngày
    create_notification(
        user,
        f" Điểm stress hôm nay của bạn: {score}",
        "stress"
    )

# =========================
# LIKE
# =========================
def notify_like(user, from_user, feedback):
    if user == from_user:
        return

    create_notification(
        user,
        f"Ai đó đã thích feedback của bạn",
        "like",
        target_url="/feedback/"
    )

# =========================
# REPLY (DEV)
# =========================
def notify_reply(user, from_user, feedback):
    create_notification(
        user,
        f" Nhà phát triển đã phản hồi feedback của bạn",
        "reply",
        target_url="/feedback/"
    )
def notify_heart(user, from_user, feedback):
    create_notification(
        user,
        f" Nhà phát triển đã thả tim feedback của bạn",
        "heart",
        target_url="/feedback/"
    )