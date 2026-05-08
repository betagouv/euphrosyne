import logging
from datetime import datetime, time, timedelta

from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone

from lab.participations.employer_workflow import (
    is_incomplete_on_premises_participation,
)
from lab.runs.models import Run
from radiation_protection.app_settings import settings as app_settings
from radiation_protection.email import (
    send_employer_information_reminder,
    send_employer_information_reminder_summary,
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Send employer information reminders for runs starting in 7 or 2 days."

    def handle(self, *args, **options):
        today = timezone.localdate()
        current_timezone = timezone.get_current_timezone()
        target_query = Q(pk__in=[])
        for days_before_run in (7, 2):
            target_date = today + timedelta(days=days_before_run)
            start = timezone.make_aware(
                datetime.combine(target_date, time.min), current_timezone
            )
            end = start + timedelta(days=1)
            target_query |= Q(start_date__gte=start, start_date__lt=end)

        runs = (
            Run.objects.filter(target_query)
            .select_related("project")
            .prefetch_related(
                "project__participation_set__user",
                "project__participation_set__institution",
                "project__participation_set__employer",
            )
        )
        self.stdout.write(
            "[send-employer-information-reminders] Found %d run(s)." % runs.count()
        )

        for run in runs:
            participations = [
                participation
                for participation in run.project.participation_set.all()
                if is_incomplete_on_premises_participation(participation)
            ]
            if not participations:
                continue

            self._send_participant_reminders(run, participations)
            self._send_additional_summary(run, participations)

    def _send_participant_reminders(self, run, participations):
        for participation in participations:
            try:
                send_employer_information_reminder(participation, run)
            except Exception as error:  # pylint: disable=broad-exception-caught
                logger.error(
                    "Failed to send employer information reminder for participation %s and run %s: %s",  # pylint: disable=line-too-long
                    participation.id,
                    run.id,
                    str(error),
                )
                continue

    def _send_additional_summary(self, run, participations):
        additional_emails = app_settings.RADIATION_PROTECTION_ADDITIONAL_NOTIFICATION_EMAILS  # type: ignore[misc] # pylint: disable=line-too-long
        if not additional_emails:
            return
        try:
            send_employer_information_reminder_summary(
                list(additional_emails), run, participations
            )
        except Exception as error:  # pylint: disable=broad-exception-caught
            logger.error(
                "Failed to send employer information reminder summary for run %s: %s",
                run.id,
                str(error),
            )
            return
