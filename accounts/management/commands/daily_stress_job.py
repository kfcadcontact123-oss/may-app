from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from datetime import date, timedelta
from chat.models import ChatMessage
import random

from stress_app.models import DailyStress
from stress_app.stress_engine import calculate_stress
from accounts.services.notification_service import create_notification
from chat.ai_service import generate_ai_reply


class Command(BaseCommand):
    def handle(self, *args, **kwargs):

        today = date.today()
        users = User.objects.all()

        for user in users:

            # 🔥 Lấy ngày cuối cùng đã có trong DB
            last_record = DailyStress.objects.filter(user=user).order_by("-created_at").first()

            if last_record:
                start_day = last_record.created_at + timedelta(days=1)
            else:
                start_day = today - timedelta(days=1)

            current_day = start_day

            while current_day < today:

                # 🔥 lấy hôm trước (để kế thừa + trend)
                yesterday = current_day - timedelta(days=1)

                yesterday_obj = DailyStress.objects.filter(
                    user=user,
                    created_at=yesterday
                ).first()

                # 🔥 lấy chat gần đây
                recent_msgs = ChatMessage.objects.filter(
                    user=user
                ).order_by("-created_at")[:6]

                message_count = len(recent_msgs)

                # =========================
                # 🔥 LOGIC SCORE (FIX QUAN TRỌNG)
                # =========================
                if message_count == 0:
                    if yesterday_obj:
                        # kế thừa + noise nhẹ
                        score = yesterday_obj.score + random.randint(-2, 2)
                        score = max(0, min(100, score))
                    else:
                        score = 30
                else:
                    score = calculate_stress(user, emotion="neutral")
                print("USER:", user.id)
                print("DATE:", current_day)
                print("MESSAGE COUNT:", message_count)
                print("YESTERDAY:", yesterday_obj.score if yesterday_obj else None)
                print("SCORE:", score)
                print("-----")

                # 🔥 diff
                diff = score - yesterday_obj.score if yesterday_obj else 0

                # 🔥 data level
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
                    feel_text = "Hôm đó bạn có vẻ khá yên tĩnh."

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

Hôm đó {trend_text}.
Bạn vẫn đang cố gắng từng chút một.
Hôm nay cứ bắt đầu nhẹ nhàng thôi nhé.
""".strip()

                # 🔥 UPDATE hoặc CREATE (không bao giờ duplicate)
                obj, created = DailyStress.objects.update_or_create(
                    user=user,
                    created_at=current_day,
                    defaults={
                        "score": score,
                        "ai_analysis": ai_text
                    }
                )

                # 🔥 notification (chỉ cho hôm qua)
                if current_day == today - timedelta(days=1):
                    create_notification(
                        user,
                        f"Điểm stress hôm qua của bạn là: {score}",
                        "stress",
                        target_url=f"/stress/{current_day}/"
                    )

                current_day += timedelta(days=1)

        self.stdout.write("DONE DAILY STRESS")
        