#đã fix
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required


# accounts/views_notification.py

@login_required
def notifications(request):
    notifs = request.user.notifications.all().order_by("-created_at")

    return render(request, "notifications.html", {
        "notifications": notifs
    })
from django.http import JsonResponse
from .models_notification import Notification

@login_required
def mark_all_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return JsonResponse({"status": "ok"})

@login_required
def delete_notification(request, id):
    Notification.objects.filter(id=id, user=request.user).delete()
    return JsonResponse({"status": "deleted"})
from django.shortcuts import render, get_object_or_404

@login_required
def notification_detail(request, id):
    notif = get_object_or_404(Notification, id=id, user=request.user)

    notif.is_read = True
    notif.save()

    if notif.target_url:
        return redirect(notif.target_url)

    # fallback (nếu không có url)
    return redirect("/")
@login_required
def notif_api(request):
    notifs = Notification.objects.filter(
        user=request.user
    ).order_by("-created_at")[:20]

    data = []

    for n in notifs:
        data.append({
            "id": n.id,
            "content": n.content,
            "is_read": n.is_read,
            "type": n.type,
            "time": n.created_at.strftime("%H:%M"),
            "url": n.target_url or ""
        })

    return JsonResponse({
        "notifications": data,
        "unread": Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()
    })