import logging
import smtplib

from django.core import mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


def send_notification(
    email: str,
    subject: str,
    template_path: str,
    certification_name: str,
    context: dict | None = None,
):
    html_message = render_to_string(template_path, context=context)
    plain_message = strip_tags(html_message)

    try:
        mail.send_mail(
            subject,
            plain_message,
            from_email=None,
            recipient_list=[email],
            html_message=html_message,
        )
    except (smtplib.SMTPException, ConnectionError) as e:
        logger.error(
            "Error sending %s certification invitation to %s. Reason: %s",
            certification_name,
            email,
            str(e),
        )
        raise e
