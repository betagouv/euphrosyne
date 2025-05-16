import logging
import typing
from functools import lru_cache

from certification.certifications.models import Certification
from certification.notifications.models import (
    CertificationNotification,
    NotificationType,
)

from .constants import RADIATION_PROTECTION_CERTIFICATION_NAME

if typing.TYPE_CHECKING:
    from euphro_auth.models import User

logger = logging.getLogger(__name__)


@lru_cache
def get_radioprotection_certification() -> Certification:
    return Certification.objects.get(name=RADIATION_PROTECTION_CERTIFICATION_NAME)


def check_radio_protection_certification(user: "User"):
    """Verify if a user has an active certification and send an invitation if not."""
    if not user_has_active_certification(user):
        create_invitation_notification(user)


def user_has_active_certification(user: "User") -> bool:
    try:
        certification = get_radioprotection_certification()
    except Certification.DoesNotExist:
        logger.error(
            "Radiation protection certification %s does not exist.",
            RADIATION_PROTECTION_CERTIFICATION_NAME,
        )
        return False
    return certification.user_has_valid_participation(user)


def create_invitation_notification(
    user: "User",
) -> CertificationNotification:
    return CertificationNotification.objects.create(
        user=user,
        certification=get_radioprotection_certification(),
        type_of=NotificationType.INVITATION_TO_COMPLETE,
    )
