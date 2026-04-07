from django.urls import path
from . import views

urlpatterns = [
    path("", views.feedback_page, name="feedback_page"),
    path("add/", views.add_feedback, name="add_feedback"),
    path("delete/<int:id>/", views.delete_feedback, name="delete_feedback"),
    path("like/<int:id>/", views.like_feedback, name="like_feedback"),
    path("dislike/<int:id>/", views.dislike_feedback, name="dislike_feedback"),
    path("heart/<int:id>/", views.heart_feedback, name="heart_feedback"),
    path("reply/<int:id>/", views.reply_feedback, name="reply_feedback"),
    path("reply/delete/<int:reply_id>/", views.delete_reply, name="delete_reply"),
]