from django.core.mail.message import EmailMultiAlternatives
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.template import loader
from django.conf import settings

from euphro_auth.models import User


def send_invitation_email(email: str, user: User, token: str):
    """
    Send a django.core.mail.EmailMultiAlternatives to `to_email`.
    """

    context = {
        "email": email,
        "site_url": settings.SITE_URL,
        "uid": urlsafe_base64_encode(force_bytes(user.pk)),
        "token": token,
    }
    subject = "[Euphrosyne] Invitation to register"
    body = loader.render_to_string("invitation_email.txt", context)

    email_message = EmailMultiAlternatives(subject=subject, body=body, to=[email])
    html_email = loader.render_to_string("invitation_email.html", context)
    email_message.attach_alternative(html_email, "text/html")

    email_message.send()
