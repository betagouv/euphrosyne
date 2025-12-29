from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from lab.admin.mixins import LabAdminAllowedMixin
from lab.permissions import is_lab_admin

from .models import ElectricalSignatureProcess, RiskPreventionPlan


class ElectricalSignatureProcessInline(admin.TabularInline):
    model = ElectricalSignatureProcess
    verbose_name = _("Related electrical signature process")
    verbose_name_plural = _("Related electrical signature processes")
    extra = 0

    fields = ("label", "status")
    readonly_fields = ("label", "status")

    def has_view_permission(self, request, obj=None):
        return is_lab_admin(request.user) or super().has_view_permission(request, obj)


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

    def get_inlines(self, request, obj):
        if obj:
            return [ElectricalSignatureProcessInline]
        return super().get_inlines(request, obj)
