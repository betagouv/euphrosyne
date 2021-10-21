from django.contrib import admin


class ModelAdmin(admin.ModelAdmin):
    class Media:
        css = {"all": ("css/euphro_admin/base.css",)}
