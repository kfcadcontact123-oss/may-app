from .models_notification import Notification   # ✅

def global_notifications(request):
    if request.user.is_authenticated:
        notifications = Notification.objects.filter(
            user=request.user
        ).order_by('-created_at')

        return {
            "notifications": notifications,
            "unread_count": notifications.filter(is_read=False).count()
        }

    return {}