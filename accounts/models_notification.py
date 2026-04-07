#đã fix
from django.contrib.auth.models import User
from django.db import models

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    content = models.TextField()
    type = models.CharField(max_length=50, default="info")
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    target_url = models.CharField(max_length=255, blank=True, null=True)