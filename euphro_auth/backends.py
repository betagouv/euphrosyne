from django.contrib.auth.backends import ModelBackend


class LowercaseEmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get("email")
        if isinstance(username, str):
            username = username.lower()
        return super().authenticate(
            request, username=username, password=password, **kwargs
        )
