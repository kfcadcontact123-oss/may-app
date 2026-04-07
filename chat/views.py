from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import ChatMessage
from .models import UserMemory
from django.shortcuts import redirect
from core.utils import get_user_memory
from accounts.models_notification import Notification

@login_required
def chat_room(request):

    messages = ChatMessage.objects.filter(
        user=request.user
    ).order_by("created_at")

    return render(request, "chat.html", {
        "messages": messages
    })