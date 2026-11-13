from django.apps import AppConfig
from django.contrib.auth.signals import user_logged_in
from django.db.models.signals import post_save


class EuphroAuthConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "euphro_auth"

    def ready(self) -> None:
        # pylint: disable=import-outside-toplevel,unused-import
        from .email_addresses import remove_stale_email_addresses
        from .jwt import schema  # noqa: F401  # registers the OpenAPI extension
        from .models import User
        from .sessions import set_session_idle_timeout

        user_logged_in.connect(
            set_session_idle_timeout,
            dispatch_uid="euphro_auth.set_session_idle_timeout",
        )
        post_save.connect(
            remove_stale_email_addresses,
            sender=User,
            dispatch_uid="euphro_auth.remove_stale_email_addresses",
        )
