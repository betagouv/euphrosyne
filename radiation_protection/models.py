from django.db import models
from django.utils.translation import gettext_lazy as _

from lab.projects.models import Participation
from lab.runs.models import Run
from shared.models import TimestampedModel


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
