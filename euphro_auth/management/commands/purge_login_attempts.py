from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone

from euphro_auth.models import LoginAttempt


class Command(BaseCommand):
    help = "Delete inactive login counters older than 24 hours."

    def handle(self, *args, **options):
        now = timezone.now()
        deleted, _ = (
            LoginAttempt.objects.filter(updated_at__lt=now - timedelta(hours=24))
            .filter(Q(locked_until__isnull=True) | Q(locked_until__lte=now))
            .delete()
        )
        self.stdout.write(f"Deleted {deleted} inactive login counters.")
