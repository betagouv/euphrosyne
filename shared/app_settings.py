"""
Reusable app-scoped settings loader.

AppLazySettings behaves like django.conf.settings, but is scoped per app and
remains unconfigured until AppConfig.ready() calls configure(). Defaults are
loaded from a module containing UPPERCASE values, then overridden by a dict
found in project settings under a single setting name.
"""

from django.conf import LazySettings, Settings, UserSettingsHolder
from django.conf import settings as dj_settings
from django.dispatch import receiver
from django.test.signals import setting_changed
from django.utils.functional import empty


class AppLazySettings(LazySettings):
    """
    Lazy app-scoped settings proxy.

    Usage pattern:
    - in <app>/app_settings.py:
        settings = AppLazySettings()
        connect_reload_signal(settings)
    - in <app>/apps.py ready():
        settings.configure(
            defaults_module="my_app.app_settings",
            project_override_name="MY_APP_SETTINGS",
        )
    - in app code:
        from my_app.app_settings import settings
        settings.MY_SETTING
    """

    __slots__ = ("_configured", "_defaults_module", "_override_name")

    def __init__(self):
        super().__init__()
        object.__setattr__(self, "_configured", False)
        object.__setattr__(self, "_defaults_module", None)
        object.__setattr__(self, "_override_name", None)

    def configure(self, default_settings=None, **options) -> None:
        defaults_module = options.pop("defaults_module", None)
        override_name = options.pop("project_override_name", None)
        if options:
            unexpected = ", ".join(sorted(options.keys()))
            raise TypeError(f"Unexpected configure options: {unexpected}")
        if defaults_module is None and isinstance(default_settings, str):
            defaults_module = default_settings
        if defaults_module is None or override_name is None:
            raise TypeError(
                "configure() requires defaults_module and project_override_name."
            )
        if default_settings is not None and not isinstance(default_settings, str):
            raise TypeError("default_settings must be a module path string if set.")

        object.__setattr__(self, "_defaults_module", defaults_module)
        object.__setattr__(self, "_override_name", override_name)
        object.__setattr__(self, "_configured", True)
        object.__setattr__(self, "_wrapped", empty)

    def _setup(self, name=None):  # pylint: disable=unused-argument
        configured = object.__getattribute__(self, "_configured")
        if not configured:
            raise RuntimeError(
                "App settings accessed before configuration. "
                "Call configure(defaults_module=..., project_override_name=...) "
                "in AppConfig.ready()."
            )

        defaults_module = object.__getattribute__(self, "_defaults_module")
        override_name = object.__getattribute__(self, "_override_name")
        base_settings = Settings(defaults_module)
        override_value = getattr(dj_settings, override_name, None)
        if override_value is None:
            object.__setattr__(self, "_wrapped", base_settings)
            return

        if not isinstance(override_value, dict):
            raise RuntimeError(f"{override_name} must be a dict of overrides.")

        holder = UserSettingsHolder(base_settings)
        for key, value in override_value.items():
            if key.isupper():
                setattr(holder, key, value)

        object.__setattr__(self, "_wrapped", holder)


def connect_reload_signal(app_settings: AppLazySettings):
    @receiver(setting_changed)
    def _reload(**kwargs):
        if not getattr(app_settings, "_configured", False):
            return
        override_name = object.__getattribute__(app_settings, "_override_name")
        if kwargs.get("setting") == override_name:
            object.__setattr__(app_settings, "_wrapped", empty)

    return _reload
