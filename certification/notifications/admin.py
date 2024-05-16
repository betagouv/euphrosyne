from django.contrib import admin
from django.http import HttpRequest

from lab.admin.mixins import LabAdminAllowedMixin

from .models import CertificationNotification


@admin.register(CertificationNotification)
class CertificationNotificationAdmin(LabAdminAllowedMixin, admin.ModelAdmin):
    list_display = ("certification", "user", "type_of", "is_sent", "created")
    fields = (
        "user",
        "certification",
        "type_of",
        "created",
        "is_sent",
        "quizz_result",
    )
    readonly_fields = ("created",)

    def has_change_permission(
        self, request: HttpRequest, obj: CertificationNotification | None = None
    ):
        return False
