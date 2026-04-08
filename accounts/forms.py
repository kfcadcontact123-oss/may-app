from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class SignUpForm(UserCreationForm):
    name = forms.CharField(label="Tên hiển thị")
    age = forms.IntegerField()
    location = forms.CharField()
    job = forms.CharField()

    class Meta:
        model = User
        fields = ("email", "password1", "password2",
                  "name", "age", "location", "job")

    def clean_email(self):
        email = self.cleaned_data.get("email").lower().strip()

        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email đã được sử dụng")

        return email