import logging
from typing import Any

from django.http import HttpRequest

from .models import User

logger = logging.getLogger(__name__)


def describe_account(email: str | None) -> str:
    """Name the account behind a sign-in address, without logging the address."""
    if email:
        pk = (
            User.objects.filter(email__iexact=email.strip())
            .values_list("pk", flat=True)
            .first()
        )
        if pk is not None:
            return f"user {pk}"
    return "unknown account"


def log_login_failure(
    sender,
    credentials: dict[str, Any],
    request: HttpRequest | None = None,
    **kwargs,
) -> None:
    # pylint: disable=unused-argument
    """Name the account targeted by a wrong password: router logs only show the
    request. Django hides the password in `credentials`; only the email is read."""
    logger.warning(
        "Password sign-in failed for %s",
        describe_account(credentials.get("email") or credentials.get("username")),
    )
