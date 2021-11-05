from django.contrib import admin

from shared.admin import ModelAdmin

from ..models import Institution


# Allowance: ADMIN:lab admin, EDITOR:lab admin, CREATOR: any user, VIEWER:any user
@admin.register(Institution)
class InstitutionAdmin(ModelAdmin):
    list_display = ("name", "country")
