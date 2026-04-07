from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models_chat_user import PrivateMessage

@login_required
def private_chat(request, user_id):
    other = get_object_or_404(User, id=user_id)

    messages = PrivateMessage.objects.filter(
        sender__in=[request.user, other],
        receiver__in=[request.user, other]
    ).order_by("created_at")

    return render(request, "private_chat.html", {
        "messages": messages,
        "other": other
    })