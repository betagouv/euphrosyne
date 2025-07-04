from django.contrib import admin

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

    def has_change_permission(self, *args, **kwargs):
        return False
