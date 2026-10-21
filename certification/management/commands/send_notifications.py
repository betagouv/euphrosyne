import logging

from django.core.management.base import BaseCommand

from ...models import CertificationNotification

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Send notifications that have not been sent yet."

    def handle(self, *args, **options):
        notifications = CertificationNotification.objects.filter(is_sent=False)
        for notification in notifications:
            if not notification.get_template_for_certification_type():
                error_message = (
                    "No template path found notification type %s"
                    " of certification %s."
                    % (
                        notification.type_of,
                        notification.certification.name,
                    )
                )
                self.stderr.write(self.style.ERROR(error_message))
                continue
            try:
                notification.send_notification()
            except Exception as e:
                error_message = (
                    "Error sending notification %s for certification %s. Reason: %s"
                    % (
                        notification.pk,
                        notification.certification.name,
                        type(e).__name__,
                    )
                )
                self.stderr.write(self.style.ERROR(error_message))
                continue
            notification.is_sent = True
            notification.save()
            self.stdout.write(
                self.style.SUCCESS(
                    "Notification %s for certification %s sent."
                    % (notification.pk, notification.certification.name)
                )
            )
