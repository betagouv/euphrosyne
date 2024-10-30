from django.test import TestCase

from lab.tests.factories import StaffUserFactory

from ..models import QuizCertification
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
