from django.urls import path
from stress_app.views import home, profile_view
from .views import stress_detail_view, latest_recap

urlpatterns = [
    path('', home, name='home'),
    path("profile/<int:user_id>/", profile_view, name="profile"),
    path("stress/<str:date>/", stress_detail_view, name="stress_detail"),
    path("recap/", latest_recap, name="latest_recap"),
]