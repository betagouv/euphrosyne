from datetime import timedelta

from django.core.management.base import BaseCommand
from django.tasks import task
from django.utils import timezone

from ...models import Run


@task
def finish_runs_task():
    now = timezone.now()
    last_friday = now - timedelta(days=now.weekday()) + timedelta(days=4, weeks=-1)
    return Run.objects.filter(
        end_date__lte=last_friday, status__lt=Run.Status.FINISHED
    ).update(status=Run.Status.FINISHED)


class Command(BaseCommand):
    help = "Set run status to finish for the ones with end dates from the privous week."

    def handle(self, *args, **options):
        result = finish_runs_task.enqueue()
        if not result.is_finished:
            self.stdout.write("finish_runs task enqueued.")
            return
        rows_cnt = result.return_value
        self.stdout.write(self.style.SUCCESS("%s finished run(s)." % rows_cnt))
