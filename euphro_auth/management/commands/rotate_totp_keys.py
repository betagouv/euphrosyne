import logging

from allauth.mfa.models import Authenticator
from django.core.management.base import BaseCommand
from django.db import transaction

from ...mfa.adapter import rotate

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = (
        "Re-encrypt every TOTP secret with the first key of "
        "MFA_TOTP_ENCRYPTION_KEYS. Run it after adding a new first key; the old "
        "key can then be removed."
    )

    def handle(self, *args, **options):
        count = 0
        with transaction.atomic():
            for authenticator in Authenticator.objects.select_for_update().filter(
                type=Authenticator.Type.TOTP
            ):
                authenticator.data["secret"] = rotate(authenticator.data["secret"])
                authenticator.save(update_fields=["data"])
                count += 1
        logger.info("TOTP secrets re-encrypted: %s", count)
        self.stdout.write(self.style.SUCCESS(f"{count} TOTP secrets re-encrypted."))
