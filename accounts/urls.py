#đã fix
from django.urls import path
from django.contrib.auth import views as auth_views
from .views import signup_view
from .views import profile_settings
from .views import delete_account
from .views import profile_view, about_view, verify_email, check_email
from .views import upload_avatar, resend_login_link
from .views_notification import *
from .views import search_user
from accounts.views import login_view, login_with_token, send_login_link
urlpatterns = [
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("signup/", signup_view, name="signup"),
    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(
            template_name="registration/password_reset.html"
        ),
        name="password_reset"
    ),

    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="registration/password_reset_done.html"
        ),
        name="password_reset_done"
    ),

    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="registration/password_reset_confirm.html"
        ),
        name="password_reset_confirm"
    ),

    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="registration/password_reset_complete.html"
        ),
        name="password_reset_complete"
    ),
    path("settings/", profile_settings, name="settings"),
    path("delete/", delete_account, name="delete_account"),
    path("profile/", profile_view, name="profile"),
    path("about/", about_view, name="about"),
    path("upload-avatar/", upload_avatar, name="upload_avatar"),
    path("notifications/", notifications),
    path("search/", search_user, name="search_user"),
    path("notif/read-all/", mark_all_read, name="notif_read_all"),
    path("notif/delete/<int:id>/", delete_notification, name="notif_delete"),
    path("notif/<int:id>/", notification_detail, name="notif_detail"),
    path("notif/api/", notif_api, name="notif_api"),
    path("verify/<uidb64>/<token>/", verify_email, name="verify_email"),
    path("check-email/", check_email, name="check_email"),
    path("login-link/", send_login_link, name="login_link"),
    path("login-token/<uidb64>/<token>/",login_with_token, name="login_with_token"),
    path("resend-login-link/", resend_login_link, name="resend_login_link"),
]