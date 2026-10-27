from collections.abc import Callable
from datetime import datetime, timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.utils.crypto import salted_hmac
from django.views.decorators.debug import sensitive_variables

from .models import LoginAttempt, User


@sensitive_variables("email", "verify_credentials")
def verify_login(
    email: str, verify_credentials: Callable[[], User | None]
) -> tuple[User | None, datetime | None]:
    """Serialize password checks for an identifier, including its first attempt."""
    identifier_hash = salted_hmac(
        "euphro_auth.login_attempt", email, algorithm="sha256"
    ).hexdigest()
    cooldown = timedelta(seconds=settings.LOGIN_LOCKOUT_SECONDS)
    with transaction.atomic():
        attempt, _ = LoginAttempt.objects.select_for_update().get_or_create(
            identifier_hash=identifier_hash
        )
        now = timezone.now()
        if attempt.locked_until and attempt.locked_until > now:
            return None, attempt.locked_until

        if attempt.locked_until or (
            attempt.last_failure_at and attempt.last_failure_at <= now - cooldown
        ):
            attempt.failures = 0
            attempt.locked_until = None

        user = verify_credentials()
        if user is None:
            attempt.failures += 1
            attempt.last_failure_at = timezone.now()
            if attempt.failures >= settings.LOGIN_FAILURE_LIMIT:
                attempt.locked_until = attempt.last_failure_at + cooldown
        else:
            attempt.failures = 0
            attempt.last_failure_at = None
            attempt.locked_until = None
        # Retain the row on success so concurrent requests keep the same lock.
        attempt.save()
        return user, attempt.locked_until
