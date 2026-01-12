import logging

import sentry_sdk
from django.core.management.base import BaseCommand
from django.tasks import task

from ...electrical_signature.electrical_signature import (
    start_electrical_signature_processes,
)
from ...models import RiskPreventionPlan

logger = logging.getLogger(__name__)


@task
def send_electrical_signature_processes_task():
    messages = []
    messages.append(
        "[send-electrical-signature-processes] Sending documents to sign..."
    )

    plans = RiskPreventionPlan.objects.filter(
        risk_advisor_notification_sent=False,
    ).all()

    messages.append(
        "[send-electrical-signature-processes] Found %d risk prevention plans to process."
        % len(plans)
    )

    for plan in plans:
        user = plan.participation.user
        sentry_sdk.set_extra("user", user.email)
        sentry_sdk.set_extra("run", plan.run.id)

        # Generate the document
        try:
            processes = start_electrical_signature_processes(plan)
            for process in processes:
                messages.append(
                    "[send-electrical-signature-processes] Started electrical signature process %s."
                    % process
                )
        except Exception as e:
            logger.error(
                "Error starting electrical signature process for plan %s: %s",
                plan.id,
                str(e),
            )
            sentry_sdk.capture_exception(e)

        # Mark the plan as sent
        plan.risk_advisor_notification_sent = True
        plan.save()
    return messages


class Command(BaseCommand):
    help = "Send documents to sign."

    def handle(self, *args, **options):
        result = send_electrical_signature_processes_task.enqueue()
        if not result.is_finished:
            self.stdout.write("send_electrical_signature_processes task enqueued.")
            return
        for message in result.return_value:
            self.stdout.write(message)
