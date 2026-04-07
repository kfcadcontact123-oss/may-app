from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class SignUpForm(UserCreationForm):
    age = forms.IntegerField()
    location = forms.CharField()
    job = forms.CharField()

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2",
                  "age", "location", "job")
    def clean_email(self):
        email = self.cleaned_data.get("email")

        if not email:
            raise forms.ValidationError("Email là bắt buộc")

        email = email.lower().strip()

        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email này đã được sử dụng.")

        return email