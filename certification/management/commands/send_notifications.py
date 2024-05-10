import logging

from django.core.management.base import BaseCommand

from ...models import CertificationNotification
from ...notifications.emails import send_notification

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Send notifications that have not been sent yet."

    def handle(self, *args, **options):
        notifications = CertificationNotification.objects.filter(is_sent=False)
        for notification in notifications:
            try:
                send_notification(
                    notification.user.email,
                    notification.get_template_for_certification_type(),
                    notification.certification.name,
                    notification.get_context_for_certification(),
                )
            except Exception as e:
                error_message = (
                    "Error sending notification for certification %s to %s. Reason: %s"
                    % (
                        notification.certification.name,
                        notification.user.email,
                        str(e),
                    )
                )
                self.stderr.write(self.style.ERROR(error_message))
                continue
            notification.is_sent = True
            notification.save()
            self.stdout.write(
                self.style.SUCCESS(
                    "Notification for certification %s sent to %s."
                    % (notification.certification.name, notification.user.email)
                )
            )
