from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from lab.tests.factories import StaffUserFactory

from ..models import QuizCertification, QuizResult
from .factories import (
    CertificationOfTypeQuizFactory,
    QuizCertificationFactory,
    QuizResultFactory,
)


class TestQuizCertificationQuerySet(TestCase):
    def test_get_next_quizzes_for_user(self):
        certification = CertificationOfTypeQuizFactory()
        q1 = QuizCertificationFactory(certification=certification, passing_score=100)
        q2 = QuizCertificationFactory(certification=certification, passing_score=100)
        q3 = QuizCertificationFactory(certification=certification, passing_score=100)

        user = StaffUserFactory()

        assert list(
            # pylint: disable=protected-access
            QuizCertification.objects.all()._get_next_quizzes_for_user(
                certification, user
            )
        ) == [q1, q2, q3]

        QuizResultFactory(user=user, quiz=q1, score=99, is_passed=False)

        assert list(
            # pylint: disable=protected-access
            QuizCertification.objects.all()._get_next_quizzes_for_user(
                certification, user
            )
        ) == [q2, q3]

        QuizResultFactory(user=user, quiz=q2, score=99, is_passed=False)

        assert list(
            # pylint: disable=protected-access
            QuizCertification.objects.all()._get_next_quizzes_for_user(
                certification, user
            )
        ) == [q3]

        QuizResultFactory(user=user, quiz=q3, score=99, is_passed=False)

        assert list(
            # pylint: disable=protected-access
            QuizCertification.objects.all()._get_next_quizzes_for_user(
                certification, user
            )
        ) == [q1, q2, q3]

        QuizResultFactory(user=user, quiz=q2, score=99, is_passed=False)

        assert list(
            # pylint: disable=protected-access
            QuizCertification.objects.all()._get_next_quizzes_for_user(
                certification, user
            )
        ) == [q1, q3]


class QuizResultQuerySetTests(TestCase):
    def test_filter_valid_results_for_user(self):
        user = StaffUserFactory()
        certification = CertificationOfTypeQuizFactory(num_days_valid=10)
        q1 = QuizCertificationFactory(certification=certification, passing_score=100)

        qr = QuizResultFactory(
            user=user,
            quiz=q1,
            score=100,
            is_passed=True,
        )

        valid_results = QuizResult.objects.filter_valid_results_for_user(
            user=user, certification=certification
        )

        assert list(valid_results) == [qr]

    def test_has_valid_certification_for_user_when_no_result(self):
        certification = CertificationOfTypeQuizFactory(num_days_valid=None)
        QuizCertificationFactory(certification=certification, passing_score=100)

        user = StaffUserFactory()

        assert not QuizResult.objects.filter_valid_results_for_user(
            user=user, certification=certification
        )

    def test_has_valid_certification_for_user_when_valid_result(self):
        certification = CertificationOfTypeQuizFactory(num_days_valid=None)
        q1 = QuizCertificationFactory(certification=certification, passing_score=100)

        user = StaffUserFactory()

        QuizResultFactory(user=user, quiz=q1, score=100, is_passed=True)

        assert QuizResult.objects.filter_valid_results_for_user(
            user=user, certification=certification
        )

    def test_has_valid_certification_for_user_when_not_passed(self):
        certification = CertificationOfTypeQuizFactory(num_days_valid=None)
        q1 = QuizCertificationFactory(certification=certification, passing_score=100)

        user = StaffUserFactory()

        QuizResultFactory(user=user, quiz=q1, score=100, is_passed=False)

        assert not QuizResult.objects.filter_valid_results_for_user(
            user=user, certification=certification
        )

    def test_has_valid_certification_for_user_when_expired_result(self):
        certification = CertificationOfTypeQuizFactory(num_days_valid=10)
        q1 = QuizCertificationFactory(certification=certification, passing_score=100)

        user = StaffUserFactory()

        qr = QuizResultFactory(
            user=user,
            quiz=q1,
            score=100,
            is_passed=True,
        )
        qr.created = timezone.now() - timedelta(days=11)
        qr.save()

        assert not QuizResult.objects.filter_valid_results_for_user(
            user=user, certification=certification
        )
