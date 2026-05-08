from django.apps import apps
from django.core import management
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Run several checks."

    def handle(self, *args, **options):
        self.stdout.write("Running checks...")
        management.call_command("check_project_data_availability")
        management.call_command("check_synced_project_folders")
        management.call_command("check_long_running_vms", "1440", "--send-alerts")
        if apps.is_installed("data_management"):
            management.call_command("schedule_project_cooling")
        if apps.is_installed("radiation_protection"):
            management.call_command("send_employer_information_reminders")
