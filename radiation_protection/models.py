from django.db import models
from django.utils.translation import gettext_lazy as _

from lab.projects.models import Participation
from lab.runs.models import Run
from shared.models import TimestampedModel

from .electrical_signature.providers.goodflag import get_status


class RiskPreventionPlan(TimestampedModel):
    """
    Model to represent a risk prevention plan for a specific run.
    """

    participation = models.ForeignKey(
        Participation, on_delete=models.CASCADE, related_name="risk_prevention_plans"
    )
    run = models.ForeignKey(
        Run,
        on_delete=models.CASCADE,
        related_name="risk_prevention_plans",
    )

    risk_advisor_notification_sent = models.BooleanField(
        default=False,
        verbose_name=_("Risk Advisor Notification Sent"),
        help_text=_("Indicates if the risk advisor has been notified about this plan."),
    )

    class Meta:
        unique_together = ("participation", "run")
        verbose_name = _("Run Risk Prevention Plan")
        verbose_name_plural = _("Run Risk Prevention Plans")

    def __str__(self):
        run_label = self.run.label
        user_email = self.participation.user.email
        return f"Risk Prevention Plan for {run_label} - {user_email}"


class ElectricalSignatureProcess(models.Model):
    """
    Model to represent an electrical signature process linked to a risk prevention plan.
    """

    label = models.CharField(
        max_length=255,
        verbose_name=_("Label"),
        help_text=_("A descriptive label for the electrical signature process."),
    )

    risk_prevention_plan = models.ForeignKey(
        RiskPreventionPlan,
        on_delete=models.CASCADE,
        related_name="electrical_signature_processes",
    )

    provider_name = models.CharField(
        max_length=100,
        verbose_name=_("Provider Name"),
        help_text=_("The name of the electrical signature service provider."),
    )
    provider_workflow_id = models.CharField(
        max_length=255,
        verbose_name=_("Provider Workflow ID"),
        help_text=_("The ID of the provider workflow associated with this process."),
    )
    is_completed = models.BooleanField(
        default=False,
        verbose_name=_("Is Completed"),
        help_text=_(
            "Indicates if the electrical signature process has been completed."
        ),
    )

    @property
    def status(self):
        if self.provider_name == "goodflag":
            return get_status(self) or ""
        return ""

    class Meta:
        verbose_name = _("Electrical Signature Process")
        verbose_name_plural = _("Electrical Signature Processes")

    def __str__(self):
        return self.label
