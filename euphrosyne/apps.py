from django.contrib.admin.apps import AdminConfig as DjangoAdminConfig


class AdminConfig(DjangoAdminConfig):
    default_site = "euphrosyne.admin.AdminSite"
