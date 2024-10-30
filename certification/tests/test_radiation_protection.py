from unittest import mock

import pytest
from django.utils import timezone

from lab.tests.factories import StaffUserFactory

from ..certifications.models import Certification, QuizCertification, QuizResult
from ..notifications.models import CertificationNotification, NotificationType
from ..radiation_protection import (
    check_radio_protection_certification,
    create_invitation_notification,
    user_has_active_certification,
)


@pytest.fixture(name="certification")
def certification_fixture():
    return Certification.objects.create(name="radiation", num_days_valid=5)


@pytest.fixture(name="quiz")
def quiz_fixture(certification):
    return QuizCertification.objects.create(
        certification=certification,
        url="url",
        passing_score=90,
    )


@pytest.mark.django_db
def test_user_has_active_certification(
    certification: Certification, quiz: QuizCertification
):
    user = StaffUserFactory()
    with mock.patch(
        "certification.radiation_protection._get_radioprotection_certification",
        return_value=certification,
    ):
        # Result with is not passed
        QuizResult.objects.create(user=user, quiz=quiz, is_passed=False, score=89)
        assert not user_has_active_certification(user)

        # Result is passed but too old
        result = QuizResult.objects.create(
            user=user,
            quiz=quiz,
            is_passed=True,
            score=95,
        )
        result.created = timezone.now() - timezone.timedelta(days=6)
        result.save()
        assert not user_has_active_certification(user)

        # Result is passed and recent
        result = QuizResult.objects.create(
            user=user,
            quiz=quiz,
            is_passed=True,
            score=95,
        )
        result.created = timezone.now() - timezone.timedelta(days=4)
        result.save()
        assert user_has_active_certification(user)


def test_user_has_active_certification_when_certification_does_not_exist():
    with mock.patch(
        "certification.radiation_protection._get_radioprotection_certification",
        side_effect=Certification.DoesNotExist,
    ):
        assert user_has_active_certification(mock.MagicMock()) is False


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
