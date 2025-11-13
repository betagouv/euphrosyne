import logging

import sentry_sdk
from django.core.management.base import BaseCommand

from ...electrical_signature.electrical_signature import (
    start_electrical_signature_processes,
)
from ...models import RiskPreventionPlan

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Send documents to sign."

    def handle(self, *args, **options):

        self.stdout.write(
            "[send-electrical-signature-processes] Sending documents to sign..."
        )

        plans = RiskPreventionPlan.objects.filter(
            risk_advisor_notification_sent=False,
        ).all()

        self.stdout.write(
            "[send-electrical-signature-processes] Found %d risk prevention plans to process."  # pylint: disable=line-too-long
            % len(plans)
        )

        for plan in plans:
            user = plan.participation.user
            sentry_sdk.set_extra("user", user.email)
            sentry_sdk.set_extra("run", plan.run.id)

            # Generate the document
            processes = start_electrical_signature_processes(plan)
            for process in processes:
                self.stdout.write(
                    "[send-electrical-signature-processes] Started electrical signature process %s."  # pylint: disable=line-too-long
                    % process
                )

            # Mark the plan as sent
            plan.risk_advisor_notification_sent = True
            plan.save()
