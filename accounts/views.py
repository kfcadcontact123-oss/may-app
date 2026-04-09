#đã fix
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from .forms import SignUpForm
from django.core.mail import send_mail
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from core.utils import get_user_memory
from .views_notification import *
from django.contrib import messages
import os
from dotenv import load_dotenv
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.urls import reverse
load_dotenv()
gmail = os.getenv("EMAIL_HOST_USER")
domain = os.getenv("DOMAIN")

from chat.models import UserMemory, VIETNAM_LOCATIONS

def signup_view(request):

    if request.method == "POST":
        form = SignUpForm(request.POST)

        if form.is_valid():
            email = form.cleaned_data.get("email")
            name = form.cleaned_data.get("name")

            if not name or name.strip() == "":
                form.add_error("name", "Vui lòng nhập tên của bạn")
                return render(request, "signup.html", {
                                        "form": form,
                                        "locations": VIETNAM_LOCATIONS
                                    })
            name = name.strip()
            password = form.cleaned_data.get("password1")

            existing_user = User.objects.filter(email=email).first()

            if existing_user:
                if not existing_user.is_active:
                    user = existing_user
                    uid = urlsafe_base64_encode(force_bytes(user.pk))
                    token = default_token_generator.make_token(user)
                    verify_link = f"{domain}{reverse('verify_email', args=[uid, token])}"

                    send_mail(
                        "Xác nhận tài khoản ở MâyAI nhé.",
                        f"Link mới của bạn:\n{verify_link}",
                        gmail,
                        [user.email],
                    )

                    return render(request, "auth/check_email.html", {
                    "message": "Email xác nhận mới đã được gửi lại"
                        })
                else:
                    form.add_error("email", "Email đã tồn tại")
                    return render(request, "signup.html", {
                        "form": form,
                        "locations": VIETNAM_LOCATIONS
                    })
            else:
                user = form.save(commit=False)
                user.username = email
                user.first_name = name.strip()
                user.is_active = False
                user.save()

            # ✅ ĐOẠN NÀY PHẢI NẰM TRONG if form.is_valid()
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            verify_link = request.build_absolute_uri(
                reverse("verify_email", args=[uid, token])
            )

            send_mail(
                "Xác nhận tài khoản ở MâyAInd nhé.",
                f"Click link để kích hoạt:\n{verify_link}",
                gmail,
                [email],
            )

            location = form.cleaned_data.get("location")
            job = form.cleaned_data.get("job")
            age = form.cleaned_data.get("age")

            UserMemory.objects.get_or_create(
                user=user,
                defaults={
                    "location": location,
                    "job": job,
                    "age": age
                }
            )

            return redirect("check_email")

        # ❗ nếu form INVALID → rơi xuống đây
        print("FORM ERROR:", form.errors)

    else:
        form = SignUpForm()

    return render(request, "signup.html", {
        "form": form,
        "locations": VIETNAM_LOCATIONS
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
        name = request.POST.get("name")
        email = request.POST.get("email")

        if name and len(name) < 150:
            user.first_name = name

        if email and "@" in email:
            user.email = email

        user.save()
        # memory
        memory.job = request.POST.get("job") or memory.job
        memory.location = request.POST.get("location") or memory.location
        age_raw = request.POST.get("age")

        try:
            age = int(age_raw)
    
            # optional: chặn giá trị vô lý
            if age < 0 or age > 120:
                age = None

        except (TypeError, ValueError):
            age = None

        memory.age = age
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
from django.contrib.auth import authenticate
from django.contrib.auth import authenticate, login

def login_view(request):
    error = None

    if request.method == "POST":
        email = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=email, password=password)

        if user is not None and user.is_active:
            login(request, user)
            return redirect("/")
        else:
            error = "Email hoặc mật khẩu không đúng"

    return render(request, "login.html", {"error": error})
def check_email(request):
    return render(request, "auth/check_email.html")
from django.utils.http import urlsafe_base64_decode

def verify_email(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except Exception:
        user = None

    if user and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()

        return render(request, "auth/verify_success.html")

    return render(request, "auth/verify_failed.html")
def send_login_link(request):
    success = None

    if request.method == "POST":
        email = request.POST.get("email")
        user = User.objects.filter(email=email).first()

        if user and user.is_active:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)

            link = request.build_absolute_uri(
                reverse("login_with_token", args=[uid, token])
            )

            send_mail(
                "Đăng nhập vào Mây",
                f"Click để đăng nhập:\n{link}",
                gmail,
                [email],
            )

        # ❗ không lộ email tồn tại hay không
        success = "Nếu email tồn tại, link đăng nhập đã được gửi"

    return render(request, "auth/login_link.html", {
        "success": success
    })
from django.utils.http import urlsafe_base64_decode

def login_with_token(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except:
        user = None

    if user and default_token_generator.check_token(user, token):
        login(request, user)
        return redirect("/")

    return render(request, "auth/invalid_link.html")