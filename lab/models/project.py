from enum import Enum
from typing import Optional

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from slugify import slugify

from shared.models import TimestampedModel

from ..validators import valid_filename
from .participation import Participation


class ProjectQuerySet(models.QuerySet):
    def only_finished(self):
        return self.filter(runs__end_date__lt=timezone.now())

    def only_public(self):
        return self.filter(confidential=False)


class ProjectManager(models.Manager):
    def get_queryset(self):
        return ProjectQuerySet(self.model, using=self._db)

    def only_finished(self):
        return self.get_queryset().only_finished()

    def only_public(self):
        return self.get_queryset().only_public()


class Project(TimestampedModel):
    """A project is a collection of runs done by the same team"""

    class Status(Enum):
        TO_SCHEDULE = 1, _("To schedule")
        SCHEDULED = 11, _("Scheduled")
        ONGOING = 21, _("Ongoing")
        FINISHED = 31, _("Finished")
        DATA_AVAILABLE = 41, _("Data available")

    class Meta:
        verbose_name = _("Project")
        verbose_name_plural = _("Projects")

    objects = ProjectManager()

    name = models.CharField(
        _("Project name"), max_length=255, unique=True, validators=[valid_filename]
    )

    slug = models.CharField(_("Project name slug"), max_length=255, unique=True)

    confidential = models.BooleanField(
        _("Confidential"),
        default=False,
        help_text=_(
            "Mark this project as confidential. This will hide it from external servicecs (Euphrosyne Diglab, ...)."
        ),
    )

    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL, through="lab.Participation", verbose_name=_("Members")
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

    is_data_available = models.BooleanField(
        _("Data available"),
        default=False,
        help_text=_("Has at least one run with data available."),
    )

    def __str__(self):
        return f"{self.name}"

    @property
    def leader(self) -> Optional["Participation"]:
        try:
            return self.participation_set.select_related("user", "institution").get(
                is_leader=True
            )
        except Participation.DoesNotExist:
            return None

    @property
    def status(self) -> Status:
        if self.is_data_available:
            return self.Status.DATA_AVAILABLE
        runs_with_start_date = self.runs.filter(start_date__isnull=False).values(
            "start_date", "end_date"
        )
        if len(runs_with_start_date):
            if any(
                run["end_date"] < timezone.now() if run["end_date"] else False
                for run in runs_with_start_date
            ):
                return self.Status.FINISHED
            if any(timezone.now() > run["start_date"] for run in runs_with_start_date):
                return self.Status.ONGOING
            return self.Status.SCHEDULED
        return self.Status.TO_SCHEDULE

    def clean(self):
        super().clean()
        slug = self._generate_slug()
        qs = Project.objects.filter(slug=slug)
        if self.id:
            qs = qs.exclude(id=self.id)
        if qs.count() >= 1:
            raise ValidationError(
                {
                    "name": ValidationError(
                        _(
                            "A project with a similar name already exists. "
                            "The slug corresponding to the name you enter is '%s' "
                            "and another project with this slug exists." % slug
                        )
                    )
                }
            )

    def save(
        self,
        force_insert: bool = False,
        force_update: bool = False,
        using: Optional[str] = None,
        update_fields: Optional[list[str]] = None,
    ) -> None:
        self.slug = self._generate_slug()
        return super().save(force_insert, force_update, using, update_fields)

    def _generate_slug(self):
        if not self.name:
            raise ValueError("Can't generate slug : project name is empty.")
        return slugify(self.name)


class BeamTimeRequest(TimestampedModel):
    """A request to use AGLAE. The request can be related to an external form."""

    class RequestType(models.TextChoices):
        FRENCH = "French", _("French")
        EUROPEAN = "European", _("European")
        C2RMF = "C2RMF"
        AGLAE = "AGLAE"

    class FormType(models.TextChoices):
        SCIENCESCALL = "Sciencescall"
        HYPERION = "IPERION"
        OSCAR = "OSCAR"

    class Meta:
        verbose_name = _("Beam time request")
        verbose_name_plural = _("Beam time requests")

    project = models.OneToOneField("lab.Project", on_delete=models.CASCADE)

    request_type = models.CharField(
        _("Request type"), max_length=45, choices=RequestType.choices
    )

    request_id = models.CharField(
        _("Request ID"),
        max_length=45,
        blank=True,
        help_text=_("ID appearing on the official form"),
    )

    problem_statement = models.TextField(
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
        choices=FormType.choices,
    )

    def __str__(self) -> str:
        return f"Request for project {self.project}"
