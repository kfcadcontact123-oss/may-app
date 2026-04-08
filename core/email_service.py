from django.core.mail import send_mail
import os
from dotenv import load_dotenv
load_dotenv()
gmail = os.getenv("EMAIL_HOST_USER")
def send_user_mail(subject, message, to):
    send_mail(subject, message, gmail, [to])