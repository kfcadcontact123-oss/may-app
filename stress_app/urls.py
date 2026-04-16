from django.urls import path
from stress_app.views import home, profile_view
from .views import stress_detail_view

urlpatterns = [
    path('', home, name='home'),
    path("profile/<int:user_id>/", profile_view, name="profile"),
    path("stress/<str:date>/", stress_detail_view, name="stress_detail")
]