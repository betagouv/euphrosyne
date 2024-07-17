import datetime
import logging
import smtplib
import typing

from django.core import mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils.translation import gettext as _

logger = logging.getLogger(__name__)


class LinkDict(typing.TypedDict):
    name: str
    url: str
    data_type: typing.Literal["raw_data", "processed_data"]


class DataEmailContext(typing.TypedDict):
    links: list[LinkDict]
    expiration_date: datetime.datetime


def send_data_request_created_email(
    email: str,
):
    subject = _("[New AGLAE] Data request received")
    template_path = "data_request/email/data-request-created.html"
    _send_mail(subject, email, template_path)


def send_data_email(
    email: str,
    context: DataEmailContext,
):
    subject = _("Your New AGLAE data links")
    template_path = "data_request/email/data-links.html"
    _send_mail(subject, email, template_path, context)


def _send_mail(
    subject: str,
    email: str,
    template_path: str,
    context: typing.Mapping[str, typing.Any] | None = None,
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
            "Error sending data request email to %s. Reason: %s",
            email,
            str(e),
        )
        raise e
