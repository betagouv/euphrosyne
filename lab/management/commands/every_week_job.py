from django.core import management
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Commands to be run every week."

    def handle(self, *args, **options):
        self.stdout.write("Running checks...")
        management.call_command("alert_end_run_embargos")
        management.call_command("finish_runs")
