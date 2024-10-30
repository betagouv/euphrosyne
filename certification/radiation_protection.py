import logging
from functools import lru_cache

from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser
from django.utils import timezone

from .certifications.models import Certification, QuizCertification, QuizResult
from .notifications.models import CertificationNotification, NotificationType

logger = logging.getLogger(__name__)


@lru_cache
def _get_radioprotection_certification() -> Certification:
    return Certification.objects.get(
        name=settings.RADIATION_PROTECTION_CERTIFICATION_NAME
    )


@lru_cache
def _get_radioprotection_quizzes() -> QuizCertification:
    return QuizCertification.objects.filter(
        certification=_get_radioprotection_certification()
    )


def check_radio_protection_certification(user: AbstractBaseUser) -> bool:
    """Verify if a user has an active certification and send an invitation if not."""
    if not user_has_active_certification(user):
        create_invitation_notification(user)


def user_has_active_certification(user: AbstractBaseUser) -> bool:
    try:
        certification = _get_radioprotection_certification()
    except Certification.DoesNotExist:
        logger.error(
            "Radiation protection certification %s does not exist.",
            settings.RADIATION_PROTECTION_CERTIFICATION_NAME,
        )
        return False
    filter_kwargs = {}
    if certification.num_days_valid:
        filter_kwargs["created__gte"] = timezone.now() - timezone.timedelta(
            days=certification.num_days_valid
        )
    return QuizResult.objects.filter(
        quiz__in=_get_radioprotection_quizzes(),
        user=user,
        is_passed=True,
        **filter_kwargs,
    ).exists()


def create_invitation_notification(
    user: AbstractBaseUser,
) -> CertificationNotification:
    return CertificationNotification.objects.create(
        user=user,
        certification=_get_radioprotection_certification(),
        type_of=NotificationType.INVITATION_TO_COMPLETE,
    )
