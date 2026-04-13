from django.shortcuts import render, redirect, get_object_or_404
from .models import Feedback, FeedbackReply, FeedbackLike
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from accounts.services.notification_service import notify_like, notify_reply, notify_heart
from django.contrib.auth.models import User
from accounts.services.notification_service import create_notification
from django.db.models import Prefetch

@login_required
def feedback_page(request):
    filter_type = request.GET.get("filter", "all")
    query = request.GET.get("q", "").strip()

    feedbacks = Feedback.objects.select_related(
        "user", "user__usermemory"
    ).prefetch_related(
        Prefetch(
            "replies",
            queryset=FeedbackReply.objects.select_related("user")
        )
    )

    # 🔍 SEARCH
    if query:
        feedbacks = feedbacks.filter(
            Q(user__username__icontains=query) |
            Q(user__first_name__icontains=query) |
            Q(content__icontains=query)
        )

    # 🔎 FILTER
    if filter_type == "mine":
        feedbacks = feedbacks.filter(user=request.user)

    feedbacks = feedbacks.order_by("-created_at")

    return render(request, "feedback/page.html", {
        "feedbacks": feedbacks,
        "query":query
    })

@login_required
def add_feedback(request):
    if request.method == "POST":
        content = request.POST.get("content")

        if content:
            Feedback.objects.create(
                user=request.user,
                content=content
            )
            dev = User.objects.get(id=1)

            if dev != request.user:
                create_notification(
                    dev,
                    f"📩 {request.user.username} đã gửi feedback mới",
                    "feedback",
                    target_url="/feedback/"
                )
    return redirect("feedback_page")


@login_required
def delete_feedback(request, id):
    fb = get_object_or_404(Feedback, id=id)

    # chỉ chủ hoặc owner (id=1) được xóa
    if request.user == fb.user or request.user.id == 1:
        fb.delete()

    return redirect("/feedback/")


@login_required
def like_feedback(request, id):
    fb = get_object_or_404(Feedback, id=id)

    obj, created = FeedbackLike.objects.get_or_create(
        user=request.user,
        feedback=fb,
        defaults={"is_like": True}
    )

    liked = False

    if not created:
        if obj.is_like:
            obj.delete()
            fb.like_count = max(0, fb.like_count - 1)
        else:
            obj.is_like = True
            obj.save()
            fb.like_count += 1
            fb.dislike_count = max(0, fb.dislike_count - 1)
            liked = True
    else:
        fb.like_count += 1
        liked = True

    fb.save()

    # 🔥 CREATE NOTIFICATION
    if liked and fb.user != request.user:
        notify_like(fb.user, request.user, fb)

    return redirect("/feedback/")
@login_required
def dislike_feedback(request, id):
    fb = get_object_or_404(Feedback, id=id)

    obj, created = FeedbackLike.objects.get_or_create(
        user=request.user,
        feedback=fb,
        defaults={"is_like": False}
    )

    if not created:
        if not obj.is_like:
            obj.delete()
            fb.dislike_count = max(0, fb.dislike_count - 1)
        else:
            obj.is_like = False
            obj.save()
            fb.dislike_count += 1
            fb.like_count = max(0, fb.like_count - 1)
    else:
        fb.dislike_count += 1

    fb.save()
    return redirect("/feedback/")


@login_required
def heart_feedback(request, id):
    fb = get_object_or_404(Feedback, id=id)

    if request.user.id == 1:
        fb.is_hearted = not fb.is_hearted
        fb.save()
        if fb.is_hearted and fb.user != request.user:
            notify_heart(fb.user, request.user, fb)

    return redirect("/feedback/")


@login_required
def reply_feedback(request, id):
    if request.user.id != 1:
        return redirect("/feedback/")

    fb = get_object_or_404(Feedback, id=id)

    if request.method == "POST":
        content = request.POST.get("content")

        if content:
            reply = FeedbackReply.objects.create(
            user=request.user,
            feedback=fb,
            content=content
            )

            # 🔥 CREATE NOTIFICATION
            if fb.user != request.user:
                notify_reply(
                user=fb.user,          # người nhận
                from_user=request.user, # dev
                feedback=fb
                )

    return redirect("/feedback/")
@login_required
def feedback_list(request):
    query = request.GET.get("q")

    feedbacks = Feedback.objects.all().select_related("user", "user__usermemory")

    if query:
        feedbacks = feedbacks.filter(
            Q(user__username__icontains=query) |
            Q(content__icontains=query)
    )

    return render(request, "feedback.html", {
        "feedbacks": feedbacks,
        "query": query
    })
from django.shortcuts import get_object_or_404, redirect

@login_required
def delete_reply(request, reply_id):
    reply = get_object_or_404(FeedbackReply, id=reply_id)

    if request.user == reply.user or request.user.is_superuser:
        reply.delete()

    return redirect("/feedback/")