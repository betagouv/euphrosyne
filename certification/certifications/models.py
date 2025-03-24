import random
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Count
from django.utils import timezone
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _

from euphro_auth.models import User


class QuizCertificationQuerySet(models.QuerySet):
    def _get_next_quizzes_for_user(self, certification: "Certification", user: User):
        quizzes = self.filter(certification=certification)
        results = (
            QuizResult.objects.filter(user=user, quiz__certification=certification)
            .values("quiz")
            .annotate(total=Count("quiz"))
            .values_list("quiz", "total")
        )
        quizzes_to_exclude = []
        if results:
            max_count = max(results, key=lambda x: x[1])[1]
            this_round_quizzes = [
                quiz_id for quiz_id, count in results if count == max_count
            ]
            if len(this_round_quizzes) != quizzes.count():
                quizzes_to_exclude = this_round_quizzes
        return self.filter(certification=certification).exclude(
            id__in=quizzes_to_exclude
        )

    def get_random_next_quizz_for_user(
        self, certification: "Certification", user: User
    ):
        quizzes = self._get_next_quizzes_for_user(certification, user)
        return quizzes[random.randint(0, len(quizzes) - 1)] if quizzes else None

    def has_valid_certification_for_user(
        self, user: User, certification: "Certification"
    ):
        base_qs_args = {
            "certification": certification,
            "quizresult__user": user,
            "quizresult__is_passed": True,
        }
        if certification.num_days_valid:
            return self.filter(
                **base_qs_args,
                quizresult__created__gte=timezone.now()
                - timedelta(days=certification.num_days_valid),
            ).exists()
        return self.filter(
            **base_qs_args,
        ).exists()


class QuizCertificationManager(models.Manager):
    def get_queryset(self):
        return QuizCertificationQuerySet(self.model, using=self._db)

    def get_random_next_quizz_for_user(
        self, certification: "Certification", user: User
    ):
        return self.get_queryset().get_random_next_quizz_for_user(
            certification=certification, user=user
        )

    def has_valid_certification_for_user(
        self, user: User, certification: "Certification"
    ):
        return self.get_queryset().has_valid_certification_for_user(
            certification=certification, user=user
        )


class QuizCertification(models.Model):
    certification = models.ForeignKey(
        "Certification", on_delete=models.CASCADE, related_name="quizzes"
    )

    url = models.URLField(
        verbose_name=_("Quiz URL"), help_text="https://tally.so/r/3jyvJ6"
    )
    passing_score = models.FloatField(verbose_name=_("Passing score"))

    objects = QuizCertificationManager()

    def __str__(self) -> str:
        return _("%s (quiz)") % self.certification.name

    class Meta:
        verbose_name = _("Quiz certification")
        verbose_name_plural = _("Quiz certifications")


class CertificationType(models.TextChoices):
    QUIZ = "QUIZ", _("Quiz")


class Certification(models.Model):
    """Model representing a certification."""

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(_("Description"), blank=True, null=True)

    type_of = models.CharField(
        _("Type of certification"),
        max_length=100,
        choices=CertificationType,
        default=CertificationType.QUIZ,
    )

    num_days_valid = models.IntegerField(
        help_text=_("Number of days the certification is valid"),
        null=True,
    )

    invitation_to_complete_email_template_path = models.CharField(
        _("Invitation to complete email template path"),
        max_length=250,
        blank=True,
        null=True,
    )
    success_email_template_path = models.CharField(
        _("Success email template path"), max_length=250, blank=True, null=True
    )

    quizzes: "QuizCertification"

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.name)

    class Meta:
        verbose_name = _("Certification")
        verbose_name_plural = _("Certifications")

    def user_has_valid_participation(self, user: User) -> bool:
        if self.type_of == CertificationType.QUIZ:
            return QuizCertification.objects.has_valid_certification_for_user(
                user=user, certification=self
            )
        raise NotImplementedError(
            gettext("Certification type %(type)s not implemented.")
            % {"type": self.type_of}
        )


class QuizResult(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    quiz = models.ForeignKey(QuizCertification, on_delete=models.CASCADE)
    score = models.FloatField(_("Score"))
    is_passed = models.BooleanField(_("Quiz passed"))

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Quiz result")
        verbose_name_plural = _("Quiz results")

    def __str__(self):
        return gettext(
            "Result for %(quiz)s - %(user)s - %(score)s - %(created)s"
            % {
                "quiz": self.quiz,
                "user": self.user,
                "score": self.score,
                "created": self.created.strftime(  # pylint: disable=no-member
                    "%Y-%m-%d %H:%M:%S"
                ),
            }
        )
