"""Multi-factor authentication (TOTP, allauth.mfa) for lab administrators."""

import logging

from allauth.account.internal.flows.login import (
    AUTHENTICATION_METHODS_SESSION_KEY,
    get_authentication_records,
    record_authentication,
)
from allauth.mfa.models import Authenticator
from django.conf import settings
from django.contrib.auth import SESSION_KEY
from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.models import Session
from django.core.cache import cache
from django.http import HttpRequest
from django.middleware.csrf import rotate_token
from django.urls import reverse
from django.utils import timezone
from django.utils.http import urlencode

from lab.permissions import is_lab_admin

from ..models import User
from .adapter import is_readable

logger = logging.getLogger(__name__)

FAILURES_CACHE_TIMEOUT = 24 * 60 * 60


def is_mfa_required(user: User | AnonymousUser) -> bool:
    """Whether a second factor is enforced for this user."""
    return bool(
        settings.MFA_ADMIN_REQUIRED and user.is_authenticated and is_lab_admin(user)
    )


def has_totp(user: User) -> bool:
    return Authenticator.objects.filter(
        user_id=user.pk, type=Authenticator.Type.TOTP
    ).exists()


def is_session_verified(request: HttpRequest, user: User | AnonymousUser) -> bool:
    """Whether this session went through a second factor for this user.

    allauth records, in the session, each authentication method used. Removing
    a factor, or a reset by a superuser, ends the user's other sessions and
    forgets the second factor of the current one (end_sessions,
    forget_verification), so the records alone are enough."""
    if not user.is_authenticated:
        return False
    return any(
        record.get("method") == "mfa"
        for record in get_authentication_records(request, user)
    )


def forget_verification(request: HttpRequest) -> None:
    """Drop the second-factor records of the current session."""
    records = request.session.get(AUTHENTICATION_METHODS_SESSION_KEY, [])
    request.session[AUTHENTICATION_METHODS_SESSION_KEY] = [
        record for record in records if record.get("method") != "mfa"
    ]


def end_sessions(user: User, keep: str | None = None) -> int:
    """Delete the user's sessions, except the one whose key is ``keep``.

    Sessions are not indexed by user: this decodes every unexpired session, which
    is fine for a rare event such as a factor removal or reset."""
    ended = 0
    sessions = Session.objects.filter(expire_date__gt=timezone.now())
    if keep:
        sessions = sessions.exclude(session_key=keep)
    for session in sessions.iterator():
        if session.get_decoded().get(SESSION_KEY) == str(user.pk):
            session.delete()
            ended += 1
    return ended


def rotate_session_keys(request: HttpRequest) -> None:
    """Renew the session key and the CSRF token of a session just verified."""
    request.session.cycle_key()
    rotate_token(request)


def mark_enrollment_verified(request: HttpRequest, authenticator) -> None:
    """Confirming the first code of a new factor verifies the session."""
    record_authentication(
        request,
        request.user,
        "mfa",
        id=authenticator.pk,
        type=authenticator.type,
        enrolled=True,
    )
    rotate_session_keys(request)


def get_mfa_url(user: User, next_url: str | None = None) -> str:
    """The step the user must complete: enrollment or verification."""
    url = reverse("mfa_reauthenticate" if has_totp(user) else "mfa_activate_totp")
    if next_url:
        url += "?" + urlencode({"next": next_url})
    return url


def _failures_key(user: User) -> str:
    return f"euphro_auth.mfa.failures:{user.pk}"


def record_failure(user: User, step: str) -> None:
    key = _failures_key(user)
    count = cache.get(key, 0) + 1
    cache.set(key, count, FAILURES_CACHE_TIMEOUT)
    logger.warning(
        "MFA %s code rejected for user %s (consecutive failures: %s)",
        step,
        user.pk,
        count,
    )


def record_success(user: User) -> None:
    cache.delete(_failures_key(user))
    logger.info("MFA verification succeeded for user %s", user.pk)


def remove_unreadable_factors(user: User) -> None:
    """Remove TOTP factors whose secret can no longer be decrypted, after a
    SECRET_KEY change: the user then sets up a new factor."""
    for authenticator in Authenticator.objects.filter(
        user_id=user.pk, type=Authenticator.Type.TOTP
    ):
        if not is_readable(authenticator.data["secret"]):
            authenticator.delete()
            logger.warning(
                "MFA TOTP of user %s removed: its secret cannot be decrypted "
                "with the current SECRET_KEY",
                user.pk,
            )


def remove_factors(user: User) -> int:
    """Superuser reset: remove the user's factors and sign them out everywhere."""
    count, _ = Authenticator.objects.filter(user_id=user.pk).delete()
    end_sessions(user)
    return count
