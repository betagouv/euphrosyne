from django.apps import AppConfig


class RadiationProtectionConfig(AppConfig):
    name = "radiation_protection"
    verbose_name = "Radiation Protection"

    def ready(self):
        # Import signals to ensure they are connected
        # pylint: disable=unused-import, import-outside-toplevel
        from . import signals  # noqa: F401
