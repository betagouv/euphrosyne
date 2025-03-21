"""Email functions for lab-related operations."""

import logging

from django.conf import settings
from django.utils.translation import gettext_lazy as _

from euphro_auth.models import User
from shared.email_utils import send_email_with_language, use_user_language

from .models import Project, Run

logger = logging.getLogger(__name__)


def send_project_invitation_email(email: str, project: Project):
    """
    Send an email with an invitation link based on a user ID and a token.

    Respects user language preferences if the user exists.
    """
    context = {
        "email": email,
        "site_url": settings.SITE_URL,
        "project_id": project.id,
        "project_name": project.name,
    }
    # Try to get the user to respect their language preference if they exist
    user = User.objects.filter(email=email).first()

    with use_user_language(user=user):
        subject = _("[Euphrosyne] Invitation to join project %s") % project.name

    send_email_with_language(
        subject=subject,
        template_name="project_invitation_email",
        context=context,
        to_emails=[email],
        user=user,
    )


def send_long_lasting_email(emails: list[str], project: Project):
    """
    Send an email to the admins if any VM has been running for a long time.

    Respects each recipient's language preference.
    """
    context = {
        "emails": emails,
        "site_url": settings.SITE_URL,
        "project_id": project.id,
        "project_name": project.name,
    }

    # Send individual emails to respect each user's language preference
    for email in emails:
        user = User.objects.filter(email=email).first()

        with use_user_language(user=user):
            subject = (
                _("[Euphrosyne] Alert: Long lasting VMs in project %s") % project.name
            )

        send_email_with_language(
            subject=subject,
            template_name="long_lasting_vm_email",
            context=context,
            to_emails=[email],
            user=user,
        )


def send_ending_embargo_email(emails: list[str], run: Run):
    """
    Send an email to the project leaders when a run is about to end its embargo.

    Respects each recipient's language preference.
    """
    context = {
        "run_label": run.label,
        "project_name": run.project.name,
        "embargo_end_date": run.embargo_date,
    }

    # Send individual emails to respect each user's language preference
    for email in emails:
        user = User.objects.filter(email=email).first()

        with use_user_language(user=user):
            subject = _(
                # pylint: disable=line-too-long
                "[Euphrosyne] End of AGLAE Data Embargo for run %(run_label)s in project %(project_name)s"
            ) % {"run_label": run.label, "project_name": run.project.name}

        send_email_with_language(
            subject=subject,
            template_name="ending_embargo_email",
            context=context,
            to_emails=[email],
            user=user,
        )
