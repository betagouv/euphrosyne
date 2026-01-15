"""Email functions for data requests."""

import datetime
import logging
import typing

from django.utils.translation import gettext as _

from euphro_auth.models import User
from euphrosyne.branding import get_branding
from shared.email_utils import send_email_with_language, use_user_language

logger = logging.getLogger(__name__)


class LinkDict(typing.TypedDict):
    """Type definition for a link in data email context."""

    name: str
    url: str
    data_type: typing.Literal["raw_data", "processed_data"]


class DataEmailContext(typing.TypedDict):
    """Type definition for the context used in data emails."""

    links: list[LinkDict]
    expiration_date: datetime.datetime


def send_data_request_created_email(email: str):
    """
    Send email notification when a data request is created.

    Respects user language preference if the user exists.
    """
    # Extract the template name without extension for our utility
    template_name = "data_request/email/data-request-created"

    # Try to get the user to respect their language preference
    user = User.objects.filter(email=email).first()
    branding = get_branding()

    with use_user_language(user=user):
        subject = _("[%(facility_name)s] Data request received") % branding.__dict__

    send_email_with_language(
        subject=subject,
        template_name=template_name,
        context={"facility_name": branding.facility_name},
        to_emails=[email],
        user=user,
    )


def send_data_email(email: str, context: DataEmailContext):
    """
    Send email with data links.

    Respects user language preference if the user exists.
    """
    template_name = "data_request/email/data-links"

    # Try to get the user to respect their language preference
    user = User.objects.filter(email=email).first()
    branding = get_branding()

    with use_user_language(user=user):
        subject = _("Your %(facility_name)s data links") % branding.__dict__

    send_email_with_language(
        subject=subject,
        template_name=template_name,
        context={**context, "facility_name": branding.facility_name},
        to_emails=[email],
        user=user,
    )
