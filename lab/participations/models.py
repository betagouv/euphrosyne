from django.conf import settings
from django.contrib.postgres.constraints import ExclusionConstraint
from django.contrib.postgres.fields import RangeOperators
from django.db import models
from django.db.models.constraints import UniqueConstraint
from django.utils.translation import gettext_lazy as _

from shared.models import TimestampedModel


class Participation(TimestampedModel):
    """JOIN table between User and Project

    A user who participates in a project is a project member (possibly leader).
    """

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    project = models.ForeignKey("lab.Project", on_delete=models.CASCADE)
    is_leader = models.BooleanField(default=False)
    institution = models.ForeignKey(
        "lab.Institution", on_delete=models.SET_NULL, null=True
    )
    employer = models.ForeignKey("lab.Employer", on_delete=models.SET_NULL, null=True)

    on_premises = models.BooleanField(
        verbose_name=_("On premises"),
        default=False,
        help_text=_("Is the user going to be at the New AGLAE facility?"),
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
    name = models.CharField(verbose_name=_("name"), max_length=255)
    country = models.CharField(
        verbose_name=_("country"), max_length=255, blank=True, null=True
    )

    ror_id = models.CharField(
        verbose_name="ROR ID",
        max_length=255,
        blank=True,
        null=True,
        help_text="Research Organization Registry ID",
    )

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["name", "country", "ror_id"],
                name="unique_name_country_rorid_per_institution",
            ),
        ]

    def __str__(self) -> str:
        if self.country:
            return f"{self.name}, {self.country}"
        return self.name


class Employer(models.Model):
    email = models.EmailField(_("email address"), blank=False)
    first_name = models.CharField(_("first name"), max_length=150, blank=False)
    last_name = models.CharField(_("last name"), max_length=150, blank=False)
    function = models.CharField(_("function"), max_length=150, blank=False)

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}"
