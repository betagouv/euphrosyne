from django.contrib import admin

from ..models import Institution


# Allowance: ADMIN:lab admin, EDITOR:lab admin, CREATOR: any user, VIEWER:any user
@admin.register(Institution)
class InstitutionAdmin(admin.ModelAdmin):
    list_display = ("name", "country")
