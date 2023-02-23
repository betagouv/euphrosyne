from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from ...models import Run


class Command(BaseCommand):
    help = "Set run status to finish for the ones with end dates from the privous week."

    def handle(self, *args, **options):
        now = timezone.now()
        last_friday = now - timedelta(days=now.weekday()) + timedelta(days=4, weeks=-1)
        rows_cnt = Run.objects.filter(
            end_date__lte=last_friday, status__lt=Run.Status.FINISHED
        ).update(status=Run.Status.FINISHED)
        self.stdout.write(self.style.SUCCESS("%s finished run(s)." % rows_cnt))
