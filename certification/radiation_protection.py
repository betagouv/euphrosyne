from functools import lru_cache

from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser
from django.utils import timezone

from .certifications.models import Certification, QuizzCertification, QuizzResult
from .notifications.models import CertificationNotification, NotificationType


@lru_cache
def _get_radioprotection_certification() -> Certification:
    return Certification.objects.get(name=settings.RADIOPROTECTION_QUIZZ_NAME)


@lru_cache
def _get_radioprotection_quizz() -> QuizzCertification:
    return QuizzCertification.objects.get(
        certification=_get_radioprotection_certification()
    )


def check_radio_protection_certification(user: AbstractBaseUser) -> bool:
    """Verify if a user has an active certification and send an invitation if not."""
    if not user_has_active_certification(user):
        create_invitation_notification(user)


def user_has_active_certification(user: AbstractBaseUser) -> bool:
    certification = _get_radioprotection_certification()
    filter_kwargs = {}
    if certification.num_days_valid:
        filter_kwargs["created__gte"] = timezone.now() - timezone.timedelta(
            days=certification.num_days_valid
        )
    return QuizzResult.objects.filter(
        quizz=_get_radioprotection_quizz(),
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
