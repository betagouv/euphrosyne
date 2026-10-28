from django.apps import AppConfig
from django.contrib.auth.signals import user_logged_in


class EuphroAuthConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "euphro_auth"

    def ready(self) -> None:
        from .sessions import (  # pylint: disable=import-outside-toplevel
            set_session_idle_timeout,
        )

        user_logged_in.connect(
            set_session_idle_timeout,
            dispatch_uid="euphro_auth.set_session_idle_timeout",
        )
