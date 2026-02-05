from django.core.management.base import BaseCommand

from data_management.scheduler import run_cooling_scheduler


class Command(BaseCommand):
    help = "Schedule eligible projects for daily cooling."

    def handle(self, *args, **options) -> None:
        enqueued_count = run_cooling_scheduler()
        self.stdout.write(
            self.style.SUCCESS(
                "Cooling scheduler completed. Enqueued %s project(s)." % enqueued_count
            )
        )
