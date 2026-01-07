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

    def configure(self, *, defaults_module: str, project_override_name: str) -> None:
        object.__setattr__(self, "_defaults_module", defaults_module)
        object.__setattr__(self, "_override_name", project_override_name)
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
            raise RuntimeError(f"{self._override_name} must be a dict of overrides.")

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
        if kwargs.get("setting") == app_settings._override_name:
            app_settings._wrapped = empty

    return _reload
