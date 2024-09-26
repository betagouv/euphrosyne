from django.core import management
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Run several checks."

    def handle(self, *args, **options):
        self.stdout.write("Running checks...")
        management.call_command("check_project_data_availability")
        management.call_command("check_synced_project_folders")
