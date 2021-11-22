from typing import Optional

from django.contrib import admin
from django.http.request import HttpRequest

from ..models import Institution
from .mixins import LabAdminAllowedMixin


# Allowance: ADMIN:lab admin, EDITOR:lab admin, CREATOR: any user, VIEWER:any user
@admin.register(Institution)
class InstitutionAdmin(LabAdminAllowedMixin, admin.ModelAdmin):
    list_display = ("name", "country")
    fields = ("name", "country")

    def has_add_permission(
        self, request: HttpRequest, obj: Optional[Institution] = None
    ) -> bool:
        # Any user can add an institution
        return True
