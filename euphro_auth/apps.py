from django.apps import AppConfig
from django.contrib.auth.signals import user_logged_in, user_login_failed


class EuphroAuthConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "euphro_auth"

    def ready(self) -> None:
        # pylint: disable=import-outside-toplevel,unused-import
        from allauth.mfa.signals import authentication_failed

        from .jwt import schema  # noqa: F401  # registers the OpenAPI extension
        from .mfa.conf import warn_if_mfa_disabled
        from .mfa.signals import log_authentication_failure
        from .sessions import set_session_idle_timeout
        from .signals import log_login_failure

        user_logged_in.connect(
            set_session_idle_timeout,
            dispatch_uid="euphro_auth.set_session_idle_timeout",
        )
        user_login_failed.connect(
            log_login_failure,
            dispatch_uid="euphro_auth.log_login_failure",
        )
        authentication_failed.connect(
            log_authentication_failure,
            dispatch_uid="euphro_auth.mfa.log_authentication_failure",
        )
        warn_if_mfa_disabled()
