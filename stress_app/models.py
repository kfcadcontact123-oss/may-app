from django.db import models
from django.contrib.auth.models import User


class DailyStress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    score = models.IntegerField(default=0)
    created_at = models.DateField(auto_now_add=True)
    ai_analysis = models.TextField(null=True, blank=True)
    class Meta:
        unique_together = ("user", "created_at")