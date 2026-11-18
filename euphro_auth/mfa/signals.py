import logging

from ..models import User

logger = logging.getLogger(__name__)


def log_authentication_failure(
    sender, user: User, reauthentication: bool = False, **kwargs
) -> None:
    # pylint: disable=unused-argument
    """Name the account targeted by a wrong code: router logs only show the
    request. allauth throttles the codes itself."""
    logger.warning(
        "MFA code rejected for user %s (%s)",
        user.pk,
        "reauthentication" if reauthentication else "sign-in",
    )
