from datetime import date, timedelta
from stress_app.models import DailyStress

def get_yesterday_stress(user):
    yesterday = date.today() - timedelta(days=1)

    obj = DailyStress.objects.filter(
        user=user,
        created_at=yesterday
    ).first()

    if obj:
        return obj.score

    return None