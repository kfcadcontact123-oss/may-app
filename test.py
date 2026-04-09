from django.contrib.auth.models import User

for u in User.objects.all():
    print(u.email, u.is_active)