from django.db import models
from django.contrib.auth.models import User


# =========================
# FEEDBACK
# =========================
class Feedback(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()

    like_count = models.IntegerField(default=0)
    dislike_count = models.IntegerField(default=0)

    # admin (id=1) có thể tim
    is_hearted = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def score(self):
        return self.like_count - self.dislike_count

    def __str__(self):
        return f"{self.user} - {self.content[:30]}"


# =========================
# REPLY
# =========================
class FeedbackReply(models.Model):
    feedback = models.ForeignKey(
        Feedback,
        on_delete=models.CASCADE,
        related_name="replies"
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} → Feedback {self.feedback.id}"


# =========================
# LIKE AND DISLIKE
# =========================
class FeedbackLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    feedback = models.ForeignKey(Feedback, on_delete=models.CASCADE)

    is_like = models.BooleanField(default=True)  
    class Meta:
        unique_together = ('user', 'feedback')