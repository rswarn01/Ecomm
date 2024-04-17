from django.conf import settings
from django.core.mail import send_mail


def send_account_activate(email, email_token):
    subject = "Account verification"
    email_from = settings.EMAIL_HOST_USER
    message = f"Hi, click on the link to activate your account http://127.0.0.1:8000/accounts/login/{email_token}"

    send_mail(subject, message, email_from, [email])
