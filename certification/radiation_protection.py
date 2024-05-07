import logging
import typing
from functools import lru_cache

from django.conf import settings

from .certifications.models import Certification
from .notifications.models import CertificationNotification, NotificationType

if typing.TYPE_CHECKING:
    from euphro_auth.models import User

logger = logging.getLogger(__name__)


@lru_cache
def _get_radioprotection_certification() -> Certification:
    return Certification.objects.get(
        name=settings.RADIATION_PROTECTION_CERTIFICATION_NAME
    )


def check_radio_protection_certification(user: "User"):
    """Verify if a user has an active certification and send an invitation if not."""
    if not user_has_active_certification(user):
        create_invitation_notification(user)


def user_has_active_certification(user: "User") -> bool:
    try:
        certification = _get_radioprotection_certification()
    except Certification.DoesNotExist:
        logger.error(
            "Radiation protection certification %s does not exist.",
            settings.RADIATION_PROTECTION_CERTIFICATION_NAME,
        )
        return False
    return certification.user_has_valid_participation(user)


def create_invitation_notification(
    user: "User",
) -> CertificationNotification:
    return CertificationNotification.objects.create(
        user=user,
        certification=_get_radioprotection_certification(),
        type_of=NotificationType.INVITATION_TO_COMPLETE,
    )
