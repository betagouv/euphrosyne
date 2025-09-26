from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from lab.admin.mixins import LabAdminAllowedMixin

from .models import RiskPreventionPlan


@admin.register(RiskPreventionPlan)
class RiskPreventionPlanAdmin(LabAdminAllowedMixin, admin.ModelAdmin):
    list_display = ("participation", "run", "created")
    fields = (
        "participation",
        "run",
        "created",
        "risk_advisor_notification_sent",
    )
    readonly_fields = ("created",)

    def changelist_view(self, request, extra_context: dict | None = None):
        extra_context = extra_context or {}
        extra_context["title"] = _("Latest published risk prevention plans")
        return super().changelist_view(request, extra_context)

    def has_change_permission(self, *args, **kwargs):
        return False
