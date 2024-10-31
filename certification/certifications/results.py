from django.contrib.auth import get_user_model

from certification.notifications.models import (
    CertificationNotification,
    NotificationType,
)

from .models import Certification, QuizResult


def create_quiz_result(
    certification_name: str, quiz_url: str, email: str, score: float
):
    user = get_user_model().objects.get(email=email)

    certification = Certification.objects.get(name=certification_name)
    quiz = certification.quizzes.get(url=quiz_url)

    is_passed = score >= quiz.passing_score
    result = QuizResult.objects.create(
        user=user, quiz=quiz, score=score, is_passed=is_passed
    )
    if is_passed:
        # Create a success notification for the user
        CertificationNotification.objects.create(
            user=user,
            certification=certification,
            type_of=NotificationType.SUCCESS,
            quiz_result=result,
        )
    else:  # Create an invitation to retake the quiz
        CertificationNotification.objects.create(
            user=user,
            certification=certification,
            type_of=NotificationType.RETRY,
            quiz_result=result,
        )
