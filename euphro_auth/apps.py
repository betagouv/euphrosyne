from django.apps import AppConfig
from django.contrib.auth.signals import user_logged_in


class EuphroAuthConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "euphro_auth"

    def ready(self) -> None:
        # pylint: disable=import-outside-toplevel,unused-import
        from allauth.mfa.signals import authenticator_used

        from .jwt import schema  # noqa: F401  # registers the OpenAPI extension
        from .mfa.conf import warn_if_mfa_disabled
        from .mfa.signals import on_authenticator_used
        from .sessions import set_session_idle_timeout

        user_logged_in.connect(
            set_session_idle_timeout,
            dispatch_uid="euphro_auth.set_session_idle_timeout",
        )
        authenticator_used.connect(
            on_authenticator_used,
            dispatch_uid="euphro_auth.mfa.on_authenticator_used",
        )
        warn_if_mfa_disabled()
