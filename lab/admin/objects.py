from typing import Optional

from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.http.request import HttpRequest
from django.utils.translation import gettext_lazy as _

from ..models import Object, ObjectGroup


class ObjectInline(admin.TabularInline):
    model = Object
    verbose_name = _("Object")
    fields = ("label", "differentiation_information")
    extra = 1

    def has_module_permission(self, request: HttpRequest) -> bool:
        return request.user.is_staff

    def has_view_permission(
        self, request: HttpRequest, obj: Optional[ObjectGroup] = None
    ) -> bool:
        return True

    def has_add_permission(
        self, request: HttpRequest, obj: Optional[ObjectGroup] = None
    ) -> bool:
        return True


@admin.register(ObjectGroup)
class ObjectGroupAdmin(ModelAdmin):
    list_display = ("label",)
    inlines = (ObjectInline,)

    def has_module_permission(self, request: HttpRequest) -> bool:
        return request.user.is_staff

    def has_view_permission(
        self, request: HttpRequest, obj: Optional[ObjectGroup] = None
    ) -> bool:
        return True

    def has_add_permission(self, request: HttpRequest) -> bool:
        return True
