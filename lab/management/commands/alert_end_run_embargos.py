from datetime import datetime, time, timedelta

import sentry_sdk
from django.core.management.base import BaseCommand
from django.utils import timezone

from lab.emails import send_ending_embargo_email

from ...models import Run


def _get_check_dates(from_in_days: int, to_in_days: int):
    """
    Calculate the date range for checking embargos.

    Args:
        from_in_days (int): Number of days from today to start the range.
        to_in_days (int): Number of days from today to end the range.

    Returns:
        tuple: A tuple containing the start and end datetime objects.
    """
    today = timezone.now().date()
    check_date_from = datetime.combine((today + timedelta(days=from_in_days)), time.min)
    check_date_to = datetime.combine((today + timedelta(days=to_in_days)), time.max)
    return check_date_from, check_date_to


def get_runs_with_embargos_ending_in_range(from_in_days: int, to_in_days: int):
    check_date_from, check_date_to = _get_check_dates(from_in_days, to_in_days)

    runs = Run.objects.filter(
        embargo_date__range=[check_date_from, check_date_to],
    )

    return runs


class Command(BaseCommand):
    help = "Alert project leaders of ending run emabrgo."

    def handle(self, *args, **options):
        self.stdout.write(
            # pylint: disable=line-too-long
            "[alert end run embargos] Querying for runs that are ending in date range from %s to %s"
            % (tuple(d.strftime("%Y/%m/%d") for d in _get_check_dates(30, 36))),
        )

        runs = get_runs_with_embargos_ending_in_range(30, 36)

        self.stdout.write(
            self.style.SUCCESS(
                "[alert end run embargos] Found %s runs" % (len(runs)),
            )
        )
        for run in runs:
            leader = run.project.leader
            if not leader:
                self.stdout.write(
                    self.style.WARNING(
                        "[alert end run embargos] No leader found for project %s."
                        % run.project
                    ),
                )
                continue
            try:
                send_ending_embargo_email(
                    emails=[run.project.leader.user.email], run=run
                )

            except Exception as e:
                self.stderr.write(
                    "[alert end run embargos] Error sending email to %s. Reason: %s"
                    % (run.project.leader.user.email, str(e))
                )
                sentry_sdk.capture_exception(e)
                continue
