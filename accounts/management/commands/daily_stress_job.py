from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from datetime import date, timedelta
from chat.models import ChatMessage

from stress_app.models import DailyStress
from stress_app.stress_engine import calculate_stress
from accounts.services.notification_service import create_notification
from chat.ai_service import generate_ai_reply


class Command(BaseCommand):
    def handle(self, *args, **kwargs):

        today = date.today()
        target_day = today - timedelta(days=1)  # 🔥 tính hôm qua

        users = User.objects.all()

        for user in users:

            # ❗ tránh duplicate
            if DailyStress.objects.filter(user=user, created_at=target_day).exists():
                continue

            # ❗ nếu chưa có data lịch sử → skip (ngày đầu)
            if DailyStress.objects.filter(user=user).count() == 0:
                continue

            # 🔥 tính điểm
            score = calculate_stress(user, emotion="neutral")

            # 🔥 lấy hôm trước nữa (để so trend)
            yesterday = target_day - timedelta(days=1)

            yesterday_obj = DailyStress.objects.filter(
                user=user,
                created_at=yesterday
            ).first()

            diff = score - yesterday_obj.score if yesterday_obj else 0

            # 🔥 lấy chat gần đây
            recent_msgs = ChatMessage.objects.filter(
                user=user
            ).order_by("-created_at")[:6]

            chat_context = "\n".join([
                f"User: {m.message}\nMây: {m.response}"
                for m in reversed(recent_msgs)
            ])

            message_count = len(recent_msgs)

            if message_count == 0:
                data_level = "none"
            elif message_count <= 2:
                data_level = "low"
            elif message_count <= 5:
                data_level = "medium"
            else:
                data_level = "high"

            # 🔥 trend
            if diff >= 15:
                trend = "increase_strong"
            elif diff >= 5:
                trend = "increase"
            elif diff <= -15:
                trend = "decrease_strong"
            elif diff <= -5:
                trend = "decrease"
            else:
                trend = "stable"

            # 🔥 AI cảm xúc
            feel_text = generate_ai_reply(
                user=user,
                mode="recap_feel"
            )

            if not feel_text or len(feel_text) < 10:
                feel_text = "Hôm nay có nhiều cảm xúc đan xen."

            if not feel_text.endswith((".", "!", "?")):
                feel_text += "."

            trend_map = {
                "increase_strong": "áp lực đang tăng lên khá rõ",
                "increase": "có vẻ áp lực tăng nhẹ",
                "decrease_strong": "mọi thứ đã dịu lại nhiều",
                "decrease": "có vẻ bạn đã nhẹ lòng hơn",
                "stable": "mọi thứ đang khá ổn định"
            }

            trend_text = trend_map.get(trend, "có một chút biến động")

            ai_text = f"""
{feel_text}

Hôm qua {trend_text}.
Bạn vẫn đang cố gắng từng chút một.
Hôm nay cứ bắt đầu nhẹ nhàng thôi nhé.
""".strip()

            # 🔥 lưu DB (CHÍNH XÁC ngày hôm qua)
            DailyStress.objects.create(
                user=user,
                score=score,
                ai_analysis=ai_text,
                created_at=target_day
            )

            # 🔥 notification
            create_notification(
                user,
                f"Điểm stress hôm qua của bạn là: {score}",
                "stress",
                target_url=f"/stress/{target_day}/"
            )

        self.stdout.write("DONE DAILY STRESS")