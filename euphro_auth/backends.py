from asgiref.sync import sync_to_async
from axes.backends import AxesStandaloneBackend
from axes.utils import reset
from django.conf import settings
from django.contrib.auth.backends import ModelBackend
from django.views.decorators.debug import sensitive_variables

from .axes import get_username


class PasswordAxesBackend(AxesStandaloneBackend):
    """Run Axes for password checks, leaving OAuth authentication independent."""

    @sensitive_variables("password", "kwargs")
    def authenticate(self, request, username=None, password=None, **kwargs):
        username = username if username is not None else kwargs.get("email")
        password_attempt = (
            isinstance(username, str)
            and bool(username.strip())
            and isinstance(password, str)
        )
        raw_request = getattr(request, "_request", request)
        if raw_request is not None:
            raw_request.axes_password_attempt = password_attempt
        if password_attempt:
            return super().authenticate(
                raw_request, username=username, password=password, **kwargs
            )
        return None

    async def aauthenticate(self, request, username=None, password=None, **kwargs):
        return await sync_to_async(self.authenticate, thread_sensitive=True)(
            request, username=username, password=password, **kwargs
        )


class LowercaseEmailBackend(ModelBackend):
    @sensitive_variables("password")
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get("email")
        if not isinstance(username, str) or not username.strip():
            return None
        if not isinstance(password, str):
            return None
        username = username.lower()
        user = super().authenticate(
            request, username=username, password=password, **kwargs
        )
        if user is not None and settings.AXES_ENABLED:
            # Basic and JWT password checks do not emit user_logged_in.
            reset(username=get_username(request, {"email": username}))
        return user

    async def aauthenticate(self, request, username=None, password=None, **kwargs):
        return await sync_to_async(self.authenticate, thread_sensitive=True)(
            request, username=username, password=password, **kwargs
        )
