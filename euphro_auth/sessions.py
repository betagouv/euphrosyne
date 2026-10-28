from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest

from lab.permissions import is_lab_admin

from .models import User


def get_session_idle_timeout(user: User | AnonymousUser) -> int:
    if is_lab_admin(user):
        return settings.SESSION_IDLE_TIMEOUT_ADMIN
    return settings.SESSION_IDLE_TIMEOUT_USER


def set_session_idle_timeout(
    sender, request: HttpRequest, user: User, **kwargs
) -> None:
    # Signal arguments are supplied by Django for every authentication backend.
    # pylint: disable=unused-argument
    request.session.set_expiry(get_session_idle_timeout(user))
