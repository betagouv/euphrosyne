from django.apps import apps
from django.core import management
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Commands to be run every 10 minutes."

    def handle(self, *args, **options):
        self.stdout.write("Running commands...")
        management.call_command("send_notifications")

        if apps.is_installed("radiation_protection"):
            management.call_command("send_electrical_signature_processes")
