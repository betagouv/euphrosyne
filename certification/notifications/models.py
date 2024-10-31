from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from ..certifications.models import Certification, QuizResult
from .emails import send_notification


class NotificationType(models.TextChoices):
    INVITATION_TO_COMPLETE = "INVITATION_TO_COMPLETE", _("Invitation to complete")
    SUCCESS = "SUCCESS", _("Success")


class CertificationNotification(models.Model):
    class Meta:
        verbose_name = _("Certification notification")
        verbose_name_plural = _("Certification notifications")

    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    certification = models.ForeignKey(Certification, on_delete=models.CASCADE)

    type_of = models.CharField(
        max_length=50,
        choices=NotificationType.choices,
    )

    is_sent = models.BooleanField(default=False)

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    quiz_result = models.OneToOneField(
        QuizResult, on_delete=models.CASCADE, null=True, blank=True
    )

    def send_notification(self):
        template_path = self.get_template_for_certification_type()
        if not template_path:
            raise ValueError("No template path found for this notification type.")
        context = self.get_context_for_certification()
        send_notification(
            email=self.user.email,  # pylint: disable=no-member
            subject=self.get_subject_for_certification_type(),
            template_path=template_path,
            certification_name=self.certification.name,
            context=context,
        )
        self.is_sent = True
        self.save()

    def get_template_for_certification_type(self):
        if self.type_of == NotificationType.INVITATION_TO_COMPLETE:
            return self.certification.invitation_to_complete_email_template_path
        if self.type_of == NotificationType.SUCCESS:
            return self.certification.success_email_template_path
        return None

    def get_context_for_certification(self):
        if self.type_of == NotificationType.INVITATION_TO_COMPLETE:
            if self.certification.quizzes.exists():
                next_quizz = self.certification.quizzes.get_random_next_quizz_for_user(
                    certification=self.certification, user=self.user
                )
                return {
                    "quiz_link": next_quizz.url,
                    "passing_score": int(next_quizz.passing_score),
                    "email": self.user.email,  # pylint: disable=no-member
                    "notification_id": self.id,
                }
            return {}
        if self.type_of == NotificationType.SUCCESS:
            if self.certification.num_days_valid:
                return {
                    "valid_until": self.quiz_result.created
                    + timezone.timedelta(days=self.certification.num_days_valid)
                }
        return {}

    def get_subject_for_certification_type(self):
        if self.type_of == NotificationType.INVITATION_TO_COMPLETE:
            return (
                _("[Euphrosyne] Invitation to complete certification %s.")
                % self.certification.name
            )
        if self.type_of == NotificationType.SUCCESS:
            return (
                _("[Euphrosyne] Certification %s completed.") % self.certification.name
            )
        return ""
