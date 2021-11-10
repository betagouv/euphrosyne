from typing import Optional

from django.conf import settings
from django.contrib.postgres.constraints import ExclusionConstraint
from django.contrib.postgres.fields import RangeOperators
from django.db import models
from django.db.models.constraints import UniqueConstraint
from django.utils.translation import gettext_lazy as _

from shared.models import TimestampedModel


class ProjectStatus(models.IntegerChoices):
    TO_SCHEDULE = 1, _("To schedule")


class BeamTimeRequestType(models.TextChoices):
    FRENCH = "French", _("French")
    EUROPEAN = "European", _("European")
    C2RMF = "C2RMF"
    AGLAE = "AGLAE"


class BeamTimeRequestFormType(models.TextChoices):
    SCIENCESCALL = "Sciencescall"
    HYPERION = "Hyperion"
    OSCAR = "OSCAR"


class Run(TimestampedModel):
    label = models.CharField(_("Run label"), max_length=255, unique=True)
    date = models.DateTimeField(
        _("Run date"),
        blank=True,
    )
    project = models.ForeignKey("lab.Project", null=False, on_delete=models.PROTECT)

    def __str__(self):
        return f"Run {self.label} on {self.date}"


class Project(TimestampedModel):
    """A project is a collection of runs done by the same team"""

    name = models.CharField(_("Project name"), max_length=255, unique=True)

    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL, through="lab.Participation"
    )
    admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="projects_as_admin",
        verbose_name=_("Administrator"),
    )

    comments = models.TextField(_("Comments"), blank=True)

    status = models.IntegerField(
        choices=ProjectStatus.choices,
        default=ProjectStatus.TO_SCHEDULE,
    )

    def __str__(self):
        return f"{self.name}"

    @property
    def leader(self) -> Optional["Participation"]:
        try:
            return self.participation_set.get(is_leader=True)
        except Participation.DoesNotExist:
            return None


class BeamTimeRequest(TimestampedModel):
    """A request to use AGLAE. The request can be related to an external form."""

    project = models.OneToOneField("lab.Project", on_delete=models.CASCADE)

    request_type = models.CharField(
        _("Request type"), max_length=45, choices=BeamTimeRequestType.choices
    )

    request_id = models.CharField(
        _("Request ID"),
        max_length=45,
        blank=True,
        help_text=_("ID appearing on the official form"),
    )

    problem_statement = models.CharField(
        _("Problem statement"),
        max_length=350,
        blank=True,
        help_text=_(
            "Description of the problematic being studied with the beam analysis"
        ),
    )

    form_type = models.CharField(
        _("Form type"),
        max_length=45,
        blank=True,
        choices=BeamTimeRequestFormType.choices,
    )

    def __str__(self) -> str:
        return f"Request for project {self.project}"


class Participation(TimestampedModel):
    """JOIN table between User and Project

    A user who participates in a project is a project member (possibly leader).
    """

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    project = models.ForeignKey("lab.Project", on_delete=models.PROTECT)
    is_leader = models.BooleanField(default=False)
    institution = models.ForeignKey(
        "lab.Institution", on_delete=models.SET_NULL, null=True
    )

    def __str__(self):
        return f"{self.user} participation in {self.project}"

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["user", "project"], name="unique_user_participation_per_project"
            ),
            ExclusionConstraint(
                name="exclude_multiple_leader_participation_per_project",
                expressions=[
                    ("project", RangeOperators.EQUAL),
                ],
                condition=models.Q(is_leader=True),
            ),
        ]


class Institution(models.Model):
    name = models.CharField(max_length=255)
    country = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self) -> str:
        if self.country:
            return f"{self.name}, {self.country}"
        return self.name
