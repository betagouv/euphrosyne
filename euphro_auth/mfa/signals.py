from django.http import HttpRequest

from ..models import User
from . import services


def on_authenticator_used(
    sender, request: HttpRequest, user: User, reauthenticated: bool = False, **kwargs
) -> None:
    # pylint: disable=unused-argument
    services.record_success(user)
