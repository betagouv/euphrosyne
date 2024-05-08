from unittest import mock

import pytest
from django.utils import timezone

from lab.tests.factories import StaffUserFactory

from ..certifications.models import Certification, QuizzCertification, QuizzResult
from ..notifications.models import CertificationNotification, NotificationType
from ..radiation_protection import (
    check_radio_protection_certification,
    create_invitation_notification,
    user_has_active_certification,
)


@pytest.fixture(name="certification")
def certification_fixture():
    return Certification.objects.create(name="radiation", num_days_valid=5)


@pytest.fixture(name="quizz")
def quizz_fixture(certification):
    return QuizzCertification.objects.create(
        certification=certification,
        url="url",
        passing_score=90,
    )


@pytest.mark.django_db
def test_user_has_active_certification(
    certification: Certification, quizz: QuizzCertification
):
    user = StaffUserFactory()
    with mock.patch(
        "certification.radiation_protection._get_radioprotection_certification",
        return_value=certification,
    ):
        user_has_active_certification(user)

        # Result with is not passed
        QuizzResult.objects.create(user=user, quizz=quizz, is_passed=False, score=89)
        assert not user_has_active_certification(user)

        # Result is passed but too old
        result = QuizzResult.objects.create(
            user=user,
            quizz=quizz,
            is_passed=True,
            score=95,
        )
        result.created = timezone.now() - timezone.timedelta(days=6)
        result.save()
        assert not user_has_active_certification(user)

        # Result is passed and recent
        result = QuizzResult.objects.create(
            user=user,
            quizz=quizz,
            is_passed=True,
            score=95,
        )
        result.created = timezone.now() - timezone.timedelta(days=4)
        result.save()
        assert user_has_active_certification(user)


@pytest.mark.django_db
def test_create_invitation_notification(certification: Certification):
    user = StaffUserFactory()
    with mock.patch(
        "certification.radiation_protection._get_radioprotection_certification",
        return_value=certification,
    ):
        notification = create_invitation_notification(user)

        assert isinstance(notification, CertificationNotification)
        assert notification.user == user
        assert notification.certification == certification
        assert notification.type_of == NotificationType.INVITATION_TO_COMPLETE


@pytest.mark.parametrize("has_active_certification", [True, False])
def test_check_radio_protection_certification_when_no_valid_result(
    has_active_certification: bool,
):
    with mock.patch(
        "certification.radiation_protection.user_has_active_certification",
        return_value=has_active_certification,
    ):
        with mock.patch(
            "certification.radiation_protection.create_invitation_notification"
        ) as create_invitation_notification_mock:
            check_radio_protection_certification(mock.MagicMock())
            assert create_invitation_notification_mock.called == (
                not has_active_certification
            )
