from django.contrib import admin


class AdminSite(admin.AdminSite):
    login_template = "euphro_admin/login.html"

    site_title = "Euphrosyne"
    site_header = "Euphrosyne"
    index_title = ""
