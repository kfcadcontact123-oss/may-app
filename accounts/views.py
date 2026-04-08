#đã fix
from django.shortcuts import render, redirect
from .forms import SignUpForm
from django.core.mail import send_mail
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from chat.models import UserMemory
from core.utils import get_user_memory
from .views_notification import *
from django.contrib import messages
import os
from dotenv import load_dotenv
load_dotenv()
gmail = os.getenv("EMAIL_HOST_USER")

from chat.models import UserMemory, VIETNAM_LOCATIONS

def signup_view(request):

    if request.method == "POST":
        form = SignUpForm(request.POST)

        if form.is_valid():
            user = form.save()

            # ✅ lấy location từ form
            location = request.POST.get("location")

            # ✅ tạo UserMemory
            UserMemory.objects.create(
                user=user,
                location=location
            )

            # ✅ AUTO LOGIN
            login(request, user)

            # ✅ SEND MAIL
            email = form.cleaned_data.get("email")

            if email:
                send_mail(
        "Tạo tài khoản thành công",
        f"Tài khoản {user.username} đã tạo thành công! Chào mừng bạn đến với web của Mây nhé!",
        gmail,
        [email],
    )

            return redirect("home")

    else:
        form = SignUpForm()

    return render(request, "signup.html", {
        "form": form,
        "locations": VIETNAM_LOCATIONS  # 👈 thêm cái này
    })
@login_required
def profile_view(request):
    memory = get_user_memory(request.user)

    return render(request, "profile.html", {
        "profile_user": request.user,
        "memory": memory
    })


def about_view(request):
    return render(request, "about.html")
@login_required
def profile_settings(request):
    user = request.user
    memory, _ = UserMemory.objects.get_or_create(user=user)

    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")

        if username and len(username) < 150:
            user.username = username

        if email and "@" in email:
            user.email = email

        user.save()
        # memory
        memory.job = request.POST.get("job") or memory.job
        memory.location = request.POST.get("location") or memory.location
        memory.age = request.POST.get("age") or memory.age
        location = request.POST.get("location")
        valid_locations = [loc[0] for loc in VIETNAM_LOCATIONS]

        if location in valid_locations:
            memory.location = location
        memory.save()
        messages.success(request, "saved")
        send_mail(
            "Cập nhật tài khoản",
            "Thông tin tài khoản đã được cập nhật. Nếu người cập nhật không phải là bạn, thì hãy kiểm tra bảo mật.",
            gmail,
            [user.email],
        )

    return render(request, "settings.html", {
        "memory": memory,
        "locations": VIETNAM_LOCATIONS 
    })
@login_required
def upload_avatar(request):
    if request.method == "POST" and request.FILES.get("avatar"):
        memory, _ = UserMemory.objects.get_or_create(user=request.user)

        file = request.FILES["avatar"]
        print("FILE:", file)
        if file and file.size < 2 * 1024 * 1024:
            memory.avatar = file
            memory.save()
            print("URL:", memory.avatar.url)
        from django.contrib import messages
        messages.success(request, "avatar_updated")
        return redirect("/accounts/settings/")

    return redirect("/accounts/settings/")
# accounts/views.py
from django.shortcuts import redirect  # nếu chưa có thì thêm trên đầu file

@login_required
def search_user(request):
    query = request.GET.get("q", "")

    return redirect(f"/?q={query}")
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash

@login_required
def change_password_custom(request):
    if request.method == "POST":
        old_password = request.POST.get("old_password")
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")

        # ❌ sai mật khẩu cũ
        if not request.user.check_password(old_password):
            messages.error(request, "Sai mật khẩu cũ")
            return redirect("change_password")

        # ❌ pass mới trùng pass cũ
        if old_password == new_password:
            messages.error(request, "Mật khẩu mới phải khác mật khẩu cũ")
            return redirect("change_password")

        # ❌ confirm sai
        if new_password != confirm_password:
            messages.error(request, "Xác nhận mật khẩu không khớp")
            return redirect("change_password")

        # ✅ đổi pass
        request.user.set_password(new_password)
        request.user.save()

        # giữ login
        update_session_auth_hash(request, request.user)

        messages.success(request, "Đổi mật khẩu thành công.")
        return redirect("change_password")

    return render(request, "auth/change_password.html")
from django.views.decorators.http import require_POST

@login_required
@require_POST
def delete_account(request):
    user = request.user

    logout(request)

    user.delete()

    return redirect("login")