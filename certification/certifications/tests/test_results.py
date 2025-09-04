import pytest

from certification.certifications.models import QuizResult
from certification.certifications.results import create_quiz_result
from certification.notifications.models import (
    CertificationNotification,
    NotificationType,
)
from lab.tests.factories import StaffUserFactory

from . import factories


@pytest.mark.django_db
def test_create_quiz_result_passed():
    user = StaffUserFactory()
    certification = factories.CertificationFactory()
    quiz = factories.QuizCertificationFactory(certification=certification)
    factories.QuizCertificationFactory(certification=certification)

    create_quiz_result(
        certification.name, quiz.url, user.email, quiz.passing_score + 10
    )

    assert QuizResult.objects.count() == 1
    result = QuizResult.objects.first()
    assert result.user == user
    assert result.quiz == quiz
    assert result.score == quiz.passing_score + 10
    assert result.is_passed is True

    assert CertificationNotification.objects.count() == 1
    notification = CertificationNotification.objects.first()
    assert notification.user == user
    assert notification.certification == certification
    assert notification.type_of == NotificationType.SUCCESS
    assert notification.quiz_result == result


@pytest.mark.django_db
def test_create_quiz_result_failed():
    user = StaffUserFactory()
    certification = factories.CertificationFactory()
    quiz = factories.QuizCertificationFactory(certification=certification)
    factories.QuizCertificationFactory(certification=certification)

    create_quiz_result(
        certification.name, quiz.url, user.email, quiz.passing_score - 10
    )

    assert QuizResult.objects.count() == 1
    result = QuizResult.objects.first()
    assert result.user == user
    assert result.quiz == quiz
    assert result.score == quiz.passing_score - 10
    assert result.is_passed is False

    assert CertificationNotification.objects.count() == 1
    notification = CertificationNotification.objects.first()
    assert notification.user == user
    assert notification.certification == certification
    assert notification.type_of == NotificationType.RETRY
    assert notification.quiz_result == result
