from django.contrib import admin


class AdminSite(admin.AdminSite):
    login_template = "euphro_admin/login.html"
    index_template = "euphro_admin/index.html"
    logout_template = "euphro_admin/logout.html"

    site_title = "Euphrosyne"
    site_header = "Euphrosyne"
    index_title = ""

    class Media:
        css = {"all": ("css/euphro_admin/base.css",)}
