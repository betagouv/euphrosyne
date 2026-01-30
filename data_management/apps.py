from django.apps import AppConfig


class DataManagementConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "data_management"

    def ready(self) -> None:
        # Import signals to ensure they are connected
        # pylint: disable=unused-import, import-outside-toplevel
        from . import signals  # noqa: F401
