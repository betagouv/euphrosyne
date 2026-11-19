import logging

from django.core.management.base import BaseCommand, CommandError

from ...mfa.services import remove_devices
from ...models import User

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = (
        "Remove the authenticator application of a user, who must set up a new one "
        "at the next login. Check the user's identity before running it."
    )

    def add_arguments(self, parser):
        parser.add_argument("email", help="Email address of the user")

    def handle(self, *args, **options):
        email = options["email"].strip()
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist as error:
            raise CommandError(f"No user with email {email}.") from error

        if not remove_devices(user):
            raise CommandError(f"{email} has no two-factor authentication set up.")

        logger.warning("MFA devices of user %s removed with reset_mfa", user.pk)
        self.stdout.write(
            self.style.SUCCESS(f"Two-factor authentication reset for {user.email}.")
        )
