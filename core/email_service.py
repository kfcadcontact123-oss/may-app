from django.core.mail import send_mail

def send_user_mail(subject, message, to):
    send_mail(subject, message, "kfcadcontact123@gmail.com", [to])