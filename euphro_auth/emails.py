from django.conf import settings
from django.core.mail.message import EmailMultiAlternatives
from django.template import loader
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import gettext_lazy as _


def send_invitation_email(email: str, user_id: int, token: str):
    """
    Send an email with an invitation link based on a user ID and a token used for
    authentication.
    """

    context = {
        "email": email,
        "site_url": settings.SITE_URL,
        "uid": urlsafe_base64_encode(force_bytes(user_id)),
        "token": token,
    }
    subject = _("[Euphrosyne] Invitation to register")
    body = loader.render_to_string("invitation_email.txt", context)

    email_message = EmailMultiAlternatives(subject=subject, body=body, to=[email])
    html_email = loader.render_to_string("invitation_email.html", context)
    email_message.attach_alternative(html_email, "text/html")

    email_message.send()
