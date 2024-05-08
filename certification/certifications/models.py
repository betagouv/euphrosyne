from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _


class QuizzCertification(models.Model):
    certification = models.OneToOneField(
        "Certification", on_delete=models.CASCADE, related_name="quizz"
    )

    url = models.URLField(
        verbose_name=_("Quizz URL"), help_text="https://tally.so/r/3jyvJ6"
    )
    passing_score = models.FloatField(verbose_name=_("Passing score"))


class CertificationType(models.TextChoices):
    QUIZZ = QuizzCertification, _("Quizz")


class Certification(models.Model):
    """Model representing a certification."""

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(_("Description"), blank=True, null=True)

    type_of = models.CharField(
        _("Type of certification"),
        max_length=100,
        choices=CertificationType,
        default=CertificationType.QUIZZ,
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

    quizz: "QuizzCertification"  # hack so pylint doesn't complain

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.name)


class QuizzResult(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    quizz = models.ForeignKey(QuizzCertification, on_delete=models.CASCADE)
    score = models.FloatField(_("Score"))
    is_passed = models.BooleanField(_("Quizz passed"))

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
