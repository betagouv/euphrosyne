from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _

from ..certifications.models import Certification, QuizzResult


class NotificationType(models.TextChoices):
    INVITATION_TO_COMPLETE = "INVITATION_TO_COMPLETE", _("Invitation to complete")
    SUCCESS = "SUCCESS", _("Success")


class CertificationNotification(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    certification = models.ForeignKey(Certification, on_delete=models.CASCADE)

    type_of = models.CharField(
        max_length=50,
        choices=NotificationType.choices,
    )

    is_sent = models.BooleanField(default=False)

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    quizz_result_id = models.ForeignKey(
        QuizzResult, on_delete=models.CASCADE, null=True, blank=True
    )
