from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from lab.admin.mixins import LabAdminAllowedMixin

from .models import CertificationNotification


@admin.register(CertificationNotification)
class CertificationNotificationAdmin(LabAdminAllowedMixin, admin.ModelAdmin):
    list_display = ("certification", "participation", "type_of", "is_sent", "created")
    fields = ("participation", "certification", "type_of", "is_sent", "created")
