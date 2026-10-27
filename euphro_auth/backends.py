from functools import partial

from asgiref.sync import sync_to_async
from django.contrib.auth.backends import ModelBackend
from django.core.exceptions import PermissionDenied
from django.views.decorators.debug import sensitive_variables

from .login_protection import verify_login


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
        user, locked_until = verify_login(
            username,
            partial(
                super().authenticate,
                request,
                username=username,
                password=password,
                **kwargs,
            ),
        )
        if locked_until is not None:
            # DRF wraps HttpRequest; response middleware receives the original.
            raw_request = getattr(request, "_request", request)
            if raw_request is not None:
                raw_request.login_locked_until = locked_until
            # Raise after the transaction commits, preserving the fifth failure.
            raise PermissionDenied("Too many login attempts")
        return user

    async def aauthenticate(self, request, username=None, password=None, **kwargs):
        return await sync_to_async(self.authenticate, thread_sensitive=True)(
            request, username=username, password=password, **kwargs
        )
