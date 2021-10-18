from django.contrib import admin


class AdminSite(admin.AdminSite):
    login_template = "euphro_admin/login.html"
