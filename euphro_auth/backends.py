from axes.backends import AxesStandaloneBackend
from axes.utils import reset
from django.conf import settings
from django.contrib.auth.backends import ModelBackend


class PasswordAxesBackend(AxesStandaloneBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        # Social Auth can resume a pipeline with POST data as the positional
        # request. Only password checks need Axes' HTTP request processing.
        if password is None:
            return None
        return super().authenticate(
            request, username=username, password=password, **kwargs
        )


class LowercaseEmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get("email")
        if isinstance(username, str):
            username = username.lower()
        user = super().authenticate(
            request, username=username, password=password, **kwargs
        )
        if user is not None and settings.AXES_ENABLED:
            # API password authentication does not emit user_logged_in.
            reset(username=user.get_username().lower())
        return user
