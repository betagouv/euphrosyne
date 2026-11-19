import logging
import typing

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import gettext_lazy as _

from shared.email_utils import send_email_with_language, use_user_language

if typing.TYPE_CHECKING:
    from euphro_auth.models import User

logger = logging.getLogger(__name__)


def send_invitation_email(user: "User"):
    """
    Send an email with an invitation link based on a user ID and a token used for
    authentication. Uses the user's preferred language if available.
    """
    token = default_token_generator.make_token(user)
    context = {
        "email": user.email,
        "site_url": settings.SITE_URL,
        "uid": urlsafe_base64_encode(force_bytes(user.id)),
        "token": token,
    }

    with use_user_language(user=user):
        subject = _("[Euphrosyne] Invitation to register")

    send_email_with_language(
        subject=subject,
        template_name="invitation_email",
        context=context,
        to_emails=[user.email],
        user=user,
    )


def send_mfa_enrolled_email(user: "User"):
    """Inform the account owner that a two-factor authentication device was
    enrolled on their account."""
    context = {
        "email": user.email,
        "site_url": settings.SITE_URL,
    }

    with use_user_language(user=user):
        subject = _("[Euphrosyne] Two-factor authentication enabled")

    sent = send_email_with_language(
        subject=subject,
        template_name="euphro_auth/mfa_enrolled_email",
        context=context,
        to_emails=[user.email],
        user=user,
    )
    if not sent:
        logger.warning("MFA enrollment email could not be sent to user %s", user.pk)
    return sent
