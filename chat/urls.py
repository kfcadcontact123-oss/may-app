from django.urls import path
from . import views
from . import api
from .views_private import private_chat
from chat.views_voice import get_voice, check_voice_exists

urlpatterns = [
    path("", views.chat_room, name="chat_room"),

    # ✅ API CHAT
    path("api/", api.chat_api, name="chat_api"),
    path("status/<int:msg_id>/", api.chat_status),

    # ✅ VOICE
    path("voice/api/", get_voice),
    path("voice/check/", check_voice_exists),
]