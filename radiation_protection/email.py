import logging

from django.conf import settings
from django.core import mail
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from euphro_auth.models import User
from radiation_protection.app_settings import settings as app_settings
from shared.email_utils import send_email_with_language, use_user_language

logger = logging.getLogger(__name__)


def notify_additional_emails(user: User) -> None:
    """
    Notify additional emails about the radiation protection document.
    """
    additional_emails = app_settings.RADIATION_PROTECTION_ADDITIONAL_NOTIFICATION_EMAILS  # type: ignore[misc] # pylint: disable=line-too-long
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


def _get_employer_completion_link(project_id: int) -> str:
    return f"{settings.SITE_URL}{reverse('participation_employer_completion', kwargs={'project_id': project_id})}"  # pylint: disable=line-too-long


def send_employer_information_reminder(participation, run) -> bool:
    user = participation.user
    context = {
        "user": user,
        "project": participation.project,
        "run": run,
        "completion_url": _get_employer_completion_link(participation.project_id),
    }
    with use_user_language(user=user):
        subject = _("Employer information required for project %s") % (
            participation.project.name
        )
    return send_email_with_language(
        subject=subject,
        template_name="radiation_protection/email/employer_information_reminder",
        context=context,
        to_emails=[user.email],
        user=user,
    )


def send_employer_information_reminder_summary(
    emails: list[str], run, participations
) -> bool:
    if not emails:
        return True
    context = {
        "run": run,
        "project": run.project,
        "participations": participations,
        "site_url": settings.SITE_URL,
    }
    subject = (
        "[Euphrosyne] Informations employeur manquantes pour le projet %s"
        % run.project.name
    )
    return send_email_with_language(
        subject=subject,
        template_name="radiation_protection/email/employer_information_reminder_summary",  # pylint: disable=line-too-long
        context=context,
        to_emails=emails,
    )
