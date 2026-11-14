"""Password lockout of the sign-in page, keyed by lowercased email.

Built on allauth's rate limits (ACCOUNT_RATE_LIMITS):

- ``login_failed`` counts attempts per email; allauth consumes one per attempt
  and gives it back on success.
- on the attempt that reaches that limit, ``login_lockout`` starts a lockout of
  the same duration, counted from that failure;
- a successful password sign-in clears the failures.

ORCID logins, existing sessions and JWT refresh do not go through the password
check and are not affected.
"""

import logging

from allauth.core.internal import ratelimit
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)

APP = "allauth.account"
LOCKOUT_ACTION = "login_lockout"
FAILURES_ACTION = "login_failed"

LOCKOUT_MESSAGE = _(
    "Password sign-in is blocked for 15 minutes after too many failed attempts. "
    "You can still log in with ORCID."
)


def lockout_key(email: str) -> str:
    """Same key as allauth's own ``login_failed`` key, without the site domain:
    the platform serves a single site."""
    return email.strip().lower()


def is_locked_out(request: HttpRequest, email: str) -> bool:
    return (
        ratelimit.consume(
            request,
            app=APP,
            action=LOCKOUT_ACTION,
            key=lockout_key(email),
            dry_run=True,
            limit_get=True,
        )
        is None
    )


def consume_attempt(request: HttpRequest, email: str):
    """Count a password attempt. Returns the usage to roll back on success, or
    ``None`` when the failure limit has already been reached."""
    return ratelimit.consume(
        request, app=APP, action=FAILURES_ACTION, key=lockout_key(email)
    )


def record_failure(request: HttpRequest, email: str) -> bool:
    """Start the lockout when this failure reaches the limit. Returns whether
    the account is now locked out."""
    key = lockout_key(email)
    limit_reached = (
        ratelimit.consume(
            request, app=APP, action=FAILURES_ACTION, key=key, dry_run=True
        )
        is None
    )
    if limit_reached:
        ratelimit.consume(request, app=APP, action=LOCKOUT_ACTION, key=key)
        logger.warning("Password sign-in locked out after repeated failures")
    return limit_reached


def reset_failures(request: HttpRequest, email: str) -> None:
    ratelimit.clear(request, app=APP, action=FAILURES_ACTION, key=lockout_key(email))
