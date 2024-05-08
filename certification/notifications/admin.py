from django.contrib import admin

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
    )
    readonly_fields = (
        "user",
        "certification",
        "type_of",
        "created",
    )
