from django.contrib import admin
from django.http import HttpRequest
from django.template.response import TemplateResponse

from lab.permissions import is_lab_admin
from .models import Standard


@admin.register(Standard)
class StandardAdmin(admin.ModelAdmin):
    list_display = ("label",)
    search_fields = ("label",)

    def has_add_permission(self, request: HttpRequest) -> bool:
        return is_lab_admin(request.user)

    def has_change_permission(
        self, request: HttpRequest, obj: Standard | None = None
    ) -> bool:
        return is_lab_admin(request.user)

    def has_delete_permission(
        self, request: HttpRequest, obj: Standard | None = None
    ) -> bool:
        return is_lab_admin(request.user)

    def has_module_permission(self, request: HttpRequest) -> bool:
        return is_lab_admin(request.user)

    def has_view_permission(
        self, request: HttpRequest, obj: Standard | None = None
    ) -> bool:
        return is_lab_admin(request.user)
