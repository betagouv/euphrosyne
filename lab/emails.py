import logging
import smtplib

from django.conf import settings
from django.core.mail.message import EmailMultiAlternatives
from django.template import loader
from django.utils.translation import gettext_lazy as _

from .models import Project, Run

logger = logging.getLogger(__name__)


def send_project_invitation_email(email: str, project: Project):
    """
    Send an email with an invitation link based on a user ID and a token used for
    authentication.
    """

    context = {
        "email": email,
        "site_url": settings.SITE_URL,
        "project_id": project.id,
        "project_name": project.name,
    }
    subject = _("[Euphrosyne] Invitation to join project %s" % project.name)
    body = loader.render_to_string("project_invitation_email.txt", context)

    email_message = EmailMultiAlternatives(subject=subject, body=body, to=[email])
    html_email = loader.render_to_string("project_invitation_email.html", context)
    email_message.attach_alternative(html_email, "text/html")

    try:
        email_message.send()
    except (smtplib.SMTPException, ConnectionError) as e:
        logger.error(
            "Error sending invitation email to %s. Reason: %s",
            email,
            str(e),
        )


def send_long_lasting_email(emails: list[str], project: Project):
    """
    Send an email to the admins if any VM has been running for a long time.
    """

    context = {
        "emails": emails,
        "site_url": settings.SITE_URL,
        "project_id": project.id,
        "project_name": project.name,
    }
    subject = _(f"[Euphrosyne] Alert: Long lasting VMs in project {project.name}")
    body = loader.render_to_string("long_lasting_vm_email.txt", context)

    email_message = EmailMultiAlternatives(subject, body, to=emails)
    html_email = loader.render_to_string("long_lasting_vm_email.html", context)
    email_message.attach_alternative(html_email, "text/html")

    try:
        email_message.send()
    except (smtplib.SMTPException, ConnectionError) as e:
        logger.error(
            "Error sending long lasting VMs email to %s.",
            emails,
            exc_info=e,
        )


def send_ending_embargo_email(emails: list[str], run: Run):
    """
    Send an email to the project leaders when a run is about to end its embargo.
    """

    context = {
        "run_label": run.label,
        "project_name": run.project.name,
        "embargo_end_date": run.embargo_date,
    }
    subject = _(
        # pylint: disable=line-too-long
        "[Euphrosyne] End of AGLAE Data Embargo for run %(run_label)s in project %(project_name)s"
    ) % {"run_label": run.label, "project_name": run.project.name}

    body = loader.render_to_string("ending_embargo_email.txt", context)

    email_message = EmailMultiAlternatives(subject, body, to=emails)
    html_email = loader.render_to_string("ending_embargo_email.html", context)
    email_message.attach_alternative(html_email, "text/html")

    try:
        email_message.send()
    except (smtplib.SMTPException, ConnectionError) as e:
        logger.error(
            "Error sending ending embargo email to %s.",
            emails,
            exc_info=e,
        )
