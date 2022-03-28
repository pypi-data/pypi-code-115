from django.core.mail import send_mail
from django.conf import settings


def send_email(subject: str, recipient_list: tuple, html_message, message=None):
    send_mail(
        subject=subject,
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=recipient_list,
        html_message=html_message,
        message=message,
    )
