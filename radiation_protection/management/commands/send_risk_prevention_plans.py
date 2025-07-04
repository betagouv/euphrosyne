import logging
from typing import cast

import sentry_sdk
from django.core.management.base import BaseCommand

from ...document import (
    fill_radiation_protection_documents,
    send_document_to_risk_advisor,
)
from ...models import RiskPreventionPlan

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Send risk prevention plans to risk advisor."

    def handle(self, *args, **options):

        self.stdout.write(
            "[send-risk-prevention-plans] Sending risk prevention "
            "plans to risk advisor..."
        )

        plans = RiskPreventionPlan.objects.filter(
            risk_advisor_notification_sent=False,
        ).all()

        self.stdout.write(
            "[send-risk-prevention-plans] Found %d risk prevention plans to process."
            % len(plans)
        )

        for plan in plans:
            user = plan.participation.user
            sentry_sdk.set_extra("user", user.email)
            sentry_sdk.set_extra("run", plan.run.id)

            # Generate the document
            documents = fill_radiation_protection_documents(
                user=user, next_user_run=plan.run
            )

            if not documents or not all(documents):
                self.stderr.write(
                    "[send-risk-prevention-plans] Failed to generate radiation "
                    "protection document for user %s" % plan.participation.user.id,
                )
                sentry_sdk.capture_message(
                    "Failed to generate radiation protection document",
                    level="error",
                )
                continue

            # After checking that all documents are not None,
            # we can cast to the correct type
            valid_documents = cast(list[tuple[str, bytes]], documents)

            # Send the document to the risk advisor
            if not send_document_to_risk_advisor(plan, valid_documents):
                sentry_sdk.capture_message(
                    "Failed to send radiation protection document to risk advisor",
                    level="error",
                )
                self.stderr.write(
                    "[send-risk-prevention-plans] Failed to send radiation "
                    "protection document to risk advisor for user %s" % user.email,
                )
                return

            # Mark the plan as sent
            plan.risk_advisor_notification_sent = True
            plan.save()

            self.stdout.write(
                "[send-risk-prevention-plans] Successfully generated and sent "
                "radiation protection document for user %s" % user.email,
            )
