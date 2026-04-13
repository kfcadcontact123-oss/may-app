from django.contrib import admin
from django.urls import path, include
from stress_app.views import home
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from stress_app.views import donate, profile_view
from accounts.views import change_password_custom

urlpatterns = [
    path('admin/', admin.site.urls),

    # AUTH SYSTEM (LOGIN / LOGOUT)
    path("accounts/", include("django.contrib.auth.urls")),

    # signup tự viết
    path("accounts/", include("accounts.urls")),

    # MAIN APP
    path('', home, name='home'),

    # CHAT
    path('chat/', include('chat.urls')),
    path("accounts/login/", auth_views.LoginView.as_view(), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    #feedback
    path("feedback/", include("feedback.urls")),
    path("donate/", donate, name="donate"),
    path("profile/<int:user_id>/", profile_view, name="profile"),
    path("accounts/change-password/", change_password_custom, name="change_password"),
    path("", include("stress_app.urls")),
]
# 🔥 PHẢI CỘNG THÊM, KHÔNG GÁN
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)