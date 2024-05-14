from django.contrib.auth import get_user_model

from certification.notifications.models import (
    CertificationNotification,
    NotificationType,
)

from .models import Certification, CertificationType, QuizzCertification, QuizzResult


def create_result(certification_name: str, email: str, score: float):
    user = get_user_model().objects.get(email=email)
    certification = Certification.objects.get(name=certification_name)

    if certification.type_of == CertificationType.QUIZZ:
        quizz = QuizzCertification.objects.get(certification=certification)
        is_passed = score >= quizz.passing_score
        result = QuizzResult.objects.create(
            user=user, quizz=quizz, score=score, is_passed=is_passed
        )
        if is_passed:
            # Create a success notification for the user
            CertificationNotification.objects.create(
                user=user,
                certification=certification,
                type_of=NotificationType.SUCCESS,
                quizz_result=result,
            )
