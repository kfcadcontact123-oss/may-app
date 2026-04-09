#đã fix
from django.db import models
from django.contrib.auth.models import User
from web_project.settings import cloudinary
from cloudinary_storage.storage import MediaCloudinaryStorage


class ChatMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    response = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
VIETNAM_LOCATIONS = [
    ("hanoi", "Hà Nội"),
    ("hcm", "TP. Hồ Chí Minh"),
    ("haiphong", "Hải Phòng"),
    ("danang", "Đà Nẵng"),
    ("cantho", "Cần Thơ"),

    ("angiang", "An Giang"),
    ("bacgiang", "Bắc Giang"),
    ("bacninh", "Bắc Ninh"),
    ("baria_vungtau", "Bà Rịa - Vũng Tàu"),
    ("bentre", "Bến Tre"),
    ("binhduong", "Bình Dương"),
    ("binhdinh", "Bình Định"),
    ("binhphuoc", "Bình Phước"),
    ("camau", "Cà Mau"),
    ("daklak", "Đắk Lắk"),
    ("dongnai", "Đồng Nai"),
    ("dongthap", "Đồng Tháp"),
    ("gialai", "Gia Lai"),
    ("hagiang", "Hà Giang"),
    ("hanam", "Hà Nam"),
    ("hatinh", "Hà Tĩnh"),
    ("hungyen", "Hưng Yên"),
    ("khanhhoa", "Khánh Hòa"),
    ("kiengiang", "Kiên Giang"),
    ("lamdong", "Lâm Đồng"),
    ("laocai", "Lào Cai"),
    ("longan", "Long An"),
    ("namdinh", "Nam Định"),
    ("nghean", "Nghệ An"),
    ("ninhbinh", "Ninh Bình"),
    ("quangninh", "Quảng Ninh"),
    ("quangngai", "Quảng Ngãi"),
    ("thanhhoa", "Thanh Hóa"),
    ("thainguyen", "Thái Nguyên"),

    ("other", "Nước ngoài"),
]
class UserMemory(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    avatar = models.ImageField(
        upload_to="avatars/",
        storage=MediaCloudinaryStorage(),
        null=True,
        blank=True
)
    personality = models.TextField(blank=True)
    main_concerns = models.TextField(blank=True)

    summary = models.TextField(blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    age = models.IntegerField(null=True, blank=True)
    job = models.CharField(max_length=100, blank=True)
    location = models.CharField(
    max_length=50,
    choices=VIETNAM_LOCATIONS,
    default="hanoi"
)
class MemoryChunk(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    content = models.TextField()
    importance = models.FloatField(default=0.5)

    created_at = models.DateTimeField(auto_now_add=True)
class VoiceUsage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    count = models.IntegerField(default=0)

    class Meta:
        unique_together = ("user", "date")