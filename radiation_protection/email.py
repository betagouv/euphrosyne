import logging

from django.conf import settings
from django.core import mail

from euphro_auth.models import User
from radiation_protection.app_settings import settings as app_settings

logger = logging.getLogger(__name__)


def notify_additional_emails(user: User) -> None:
    """
    Notify additional emails about the radiation protection document.
    """
    additional_emails = app_settings.RADIATION_PROTECTION_ADDITIONAL_NOTIFICATION_EMAILS
    if not additional_emails:
        return

    user_full_name = user.get_full_name()
    subject = f"Nouveau certificat de formation aux risques pour {user_full_name}"

    plain_message = f"Bonjour,\n{user_full_name} vient d'obtenir son certificat de formation aux risques présents à AGLAE.\nBisous\nEuphrosyne\n"  # pylint: disable=line-too-long

    try:
        email = mail.EmailMultiAlternatives(
            subject=subject,
            body=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=additional_emails,
        )
        email.send()
    except Exception as e:
        logger.error(
            "Failed to notify additional emails about radiation protection "
            "document for user %s: %s",
            user.id,
            str(e),
        )
