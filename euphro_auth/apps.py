from django.apps import AppConfig
from django.contrib.auth.signals import user_logged_in


class EuphroAuthConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "euphro_auth"

    def ready(self) -> None:
        # pylint: disable=import-outside-toplevel,unused-import
        from .jwt import schema  # noqa: F401  # registers the OpenAPI extension
        from .sessions import set_session_idle_timeout

        user_logged_in.connect(
            set_session_idle_timeout,
            dispatch_uid="euphro_auth.set_session_idle_timeout",
        )

        from .mfa.conf import (  # pylint: disable=import-outside-toplevel
            warn_if_mfa_disabled,
        )

        warn_if_mfa_disabled()
