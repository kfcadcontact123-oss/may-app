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
    ("hue", "Huế"),
    ("cantho", "Cần Thơ"),

    ("tuyenquang", "Tuyên Quang"),
    ("caobang", "Cao Bằng"),
    ("laichau", "Lai Châu"),
    ("laocai", "Lào Cai"),
    ("thainguyen", "Thái Nguyên"),
    ("dienbien", "Điện Biên"),
    ("langson", "Lạng Sơn"),
    ("sonla", "Sơn La"),

    ("quangninh", "Quảng Ninh"),
    ("thanhhoa", "Thanh Hóa"),
    ("nghean", "Nghệ An"),
    ("hatinh", "Hà Tĩnh"),

    ("phutho", "Phú Thọ"),
    ("ninhbinh", "Ninh Bình"),
    ("hungyen", "Hưng Yên"),
    ("bacninh", "Bắc Ninh"),

    ("quangngai", "Quảng Ngãi"),
    ("quangtri", "Quảng Trị"),
    ("khanhhoa", "Khánh Hòa"),
    ("daklak", "Đắk Lắk"),
    ("gialai", "Gia Lai"),
    ("lamdong", "Lâm Đồng"),

    ("dongnai", "Đồng Nai"),
    ("tayninh", "Tây Ninh"),
    ("angiang", "An Giang"),
    ("dongthap", "Đồng Tháp"),
    ("vinhlong", "Vĩnh Long"),
    ("camau", "Cà Mau"),

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