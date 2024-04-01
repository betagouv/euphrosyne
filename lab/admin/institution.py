from typing import Optional

from django.contrib import admin
from django.http.request import HttpRequest

from lab.models.participation import Participation

from ..models import Institution
from .mixins import LabAdminAllowedMixin


class ParticipationInline(admin.TabularInline):
    model = Participation
    verbose_name = "Institution member"
    verbose_name_plural = "Institution members"
    extra = 0

    fields = ("user",)

    def has_change_permission(
        self, request: HttpRequest, obj: Institution | None = None
    ) -> bool:
        return False

    def has_delete_permission(
        self, request: HttpRequest, obj: Institution | None = None
    ) -> bool:
        return False

    def has_add_permission(
        self, request: HttpRequest, obj: Institution | None = None
    ) -> bool:
        return False


# Allowance: ADMIN:lab admin, EDITOR:lab admin, CREATOR: any user, VIEWER:any user
@admin.register(Institution)
class InstitutionAdmin(LabAdminAllowedMixin, admin.ModelAdmin):
    list_display = ("name", "country", "ror_id", "members_num")
    fields = ("name", "country", "ror_id")
    inlines = [ParticipationInline]

    def has_add_permission(
        self, request: HttpRequest, obj: Optional[Institution] = None
    ) -> bool:
        # Any user can add an institution
        return True

    @admin.display
    def members_num(self, obj: Participation) -> int:
        return obj.participation_set.count()
