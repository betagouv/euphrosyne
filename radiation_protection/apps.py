from django.apps import AppConfig

from .app_settings import settings as app_settings


class RadiationProtectionConfig(AppConfig):
    name = "radiation_protection"
    verbose_name = "Radiation Protection"

    def ready(self):
        app_settings.configure(
            defaults_module="radiation_protection.app_settings",
            project_override_name="RADIATION_PROTECTION_SETTINGS",
        )
        # Import signals to ensure they are connected
        # pylint: disable=unused-import, import-outside-toplevel
        from . import signals  # noqa: F401
