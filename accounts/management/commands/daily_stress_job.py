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
        yesterday = today - timedelta(days=1)

        users = User.objects.all()

        for user in users:

            # 🔥 tính điểm
            score = calculate_stress(user, emotion="neutral")

            # 🔥 lấy hôm qua
            yesterday_obj = DailyStress.objects.filter(
                user=user,
                created_at=yesterday
            ).first()
            if yesterday_obj:
                diff = score - yesterday_obj.score
            else:
                diff = 0

            recent_msgs = ChatMessage.objects.filter(
                user=user
            ).order_by("-created_at")[:6]  # 🔥 giảm còn 6 cho chất lượng

            chat_context = "\n".join([
                f"User: {m.message}\nMây: {m.response}"
                for m in reversed(recent_msgs)
            ])

            # =============================
            # 🔥 LENGTH HINT (QUAN TRỌNG)
            # =============================
            message_count = len(recent_msgs)

            if message_count == 0:
                data_level = "none"
            elif message_count <= 2:
                data_level = "low"
            elif message_count <= 5:
                data_level = "medium"
            else:
                data_level = "high"

            # 🔥 phân loại biến động stress
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

            extra_context = f"""
CHAT:
{chat_context}

META:
- score_today: {score}
- score_yesterday: {yesterday_obj.score if yesterday_obj else "N/A"}
- diff: {diff}
- trend: {trend}
- message_count: {message_count}
- data_level: {data_level}

HƯỚNG DẪN:
- BẮT BUỘC phải nhắc đến xu hướng stress (tăng/giảm/ổn định)
- Nếu tăng mạnh → nói rõ có biến động đáng chú ý
- Nếu giảm → nói theo hướng tích cực
- Nếu ổn định → nói trạng thái cân bằng
"""

            # =============================
            # 🔥 AI chỉ generate 1 câu cảm xúc
            # =============================
            feel_text = generate_ai_reply(
                user=user,
                mode="recap_feel"
                )
            # =============================
            # 🔥 TEMPLATE SYSTEM
            # =============================

            trend_map = {
                    "increase_strong": "áp lực đang tăng lên khá rõ",
                    "increase": "có vẻ áp lực tăng nhẹ",
                    "decrease_strong": "mọi thứ đã dịu lại nhiều",
                    "decrease": "có vẻ bạn đã nhẹ lòng hơn",
                    "stable": "mọi thứ đang khá ổn định"
                    }

            trend_text = trend_map.get(trend, "có một chút biến động")

            # 👉 fallback nếu AI lỗi
            if not feel_text or len(feel_text) < 10:
                feel_text = "Hôm nay có nhiều cảm xúc đan xen."

            # 👉 đảm bảo kết thúc câu
            if not feel_text.endswith((".", "!", "?")):
                feel_text += "."
            ai_text = f"""
{feel_text}

Hôm nay {trend_text}.
Dù có lúc chưa thoải mái, bạn vẫn đang cố gắng từng chút một.
Tối nay thử nghỉ ngơi nhẹ một chút nhé.
Ngày mai cứ bắt đầu chậm thôi, không cần vội.
""".strip()
            import random

            endings = [
    "Mây vẫn ở đây với bạn.",
    "Không sao đâu, cứ từ từ thôi nhé.",
    "Bạn không cần phải làm mọi thứ hoàn hảo đâu."
]

            ending = endings[hash(user.id) % len(endings)]
            ai_text += "\n" + ending

            print("========== DEBUG AI ==========")
            print("AI TEXT RAW:\n", repr(ai_text))
            print("========== END ==========")

            # 🔥 lưu DB
            obj = DailyStress.objects.filter(
                user=user,
                created_at=today
            ).first()

            if obj:
                obj.score = score
                obj.ai_analysis = ai_text
                obj.save()
            else:
                DailyStress.objects.create(
                    user=user,
                    score=score,
                    ai_analysis=ai_text
                )

            # 🔥 notification (chỉ tóm tắt)
            create_notification(
                user,
                f"Điểm căng thẳng hôm nay của bạn là: {score}, xem chi tiết để biết thêm.",
                "stress",
                target_url=f"/stress/{today}/"
            )

        self.stdout.write("DONE DAILY STRESS")