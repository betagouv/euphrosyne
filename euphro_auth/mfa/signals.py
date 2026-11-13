from django.http import HttpRequest

from ..models import User
from . import services


def on_authenticator_used(
    sender, request: HttpRequest, user: User, reauthenticated: bool = False, **kwargs
) -> None:
    # pylint: disable=unused-argument
    services.record_success(user)
    if reauthenticated and request.user.is_authenticated:
        # A signed-in session that has just been verified. At sign-in, Django's
        # login() renews the session key and the CSRF token itself.
        services.rotate_session_keys(request)
