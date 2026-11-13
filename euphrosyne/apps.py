from django.contrib.admin.apps import AdminConfig as DjangoAdminConfig


class AdminConfig(DjangoAdminConfig):
    default_site = "euphrosyne.admin.AdminSite"

    def ready(self) -> None:
        super().ready()
        # pylint: disable=import-outside-toplevel
        from django.contrib import admin

        from euphrosyne.admin import allauth_models_without_admin

        # After autodiscovery: allauth registers these admins in its own apps.
        for model in allauth_models_without_admin():
            if admin.site.is_registered(model):
                admin.site.unregister(model)
