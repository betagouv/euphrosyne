from enum import Enum
from typing import Optional

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Prefetch, QuerySet
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from slugify import slugify

from euphro_auth.models import User
from lab.participations.models import Participation
from lab.runs.models import Run
from lab.validators import valid_filename
from shared.models import TimestampedModel


class ProjectQuerySet(models.QuerySet):
    def has_to_schedule_runs(self):
        return self.filter(runs__start_date__isnull=True)

    def only_to_schedule(self):
        to_schedule_runs = Run.objects.filter(start_date__isnull=False)
        return self.exclude(runs__in=to_schedule_runs)

    def only_finished(self):
        return self.filter(runs__end_date__lt=timezone.now())

    def only_public(self):
        has_accepted_cgu_leader_participations = Participation.objects.filter(
            is_leader=True, user__in=User.objects.filter_has_accepted_cgu()
        )
        return self.filter(confidential=False, runs__isnull=False).filter(
            participation__in=has_accepted_cgu_leader_participations
        )

    def filter_by_status(self, status: "Project.Status"):
        if status == Project.Status.TO_SCHEDULE:
            return self.filter(runs__start_date__isnull=True)
        if status == Project.Status.SCHEDULED:
            return self.filter(runs__start_date__gte=timezone.now())
        if status == Project.Status.ONGOING:
            return self.filter(
                runs__start_date__lte=timezone.now(), runs__end_date__gte=timezone.now()
            )
        if status == Project.Status.FINISHED:
            return self.filter(
                runs__end_date__lt=timezone.now(), is_data_available=False
            )
        if status == Project.Status.DATA_AVAILABLE:
            return self.filter(is_data_available=True)
        raise ValueError(f"Unknown status {status}")

    def annotate_first_run_date(self):
        return self.annotate(first_run_date=models.Min("runs__start_date"))

    def with_prefetched_leaders(self):
        """
        Prefetch the leader participations for the projects in this queryset.

        This optimization helps reduce database queries
        when accessing the project leader.
        """
        leader_prefetch = Prefetch(
            "participation_set",
            queryset=Participation.objects.filter(is_leader=True).select_related(
                "user", "institution"
            ),
            to_attr="prefetched_leaders",
        )
        return self.prefetch_related(leader_prefetch)


class ProjectManager(models.Manager):
    def get_queryset(self):
        return ProjectQuerySet(self.model, using=self._db)

    def only_finished(self):
        return self.get_queryset().only_finished()

    def only_public(self):
        return self.get_queryset().only_public()

    def only_to_schedule(self):
        return self.get_queryset().only_to_schedule()

    def filter_by_status(self, status: "Project.Status"):
        return self.get_queryset().filter_by_status(status)

    def annotate_first_run_date(self):
        return self.get_queryset().annotate_first_run_date()

    def with_prefetched_leaders(self):
        """
        Prefetch the leader participations for all projects.

        This optimization helps reduce database queries
        when accessing the project leader.
        """
        return self.get_queryset().with_prefetched_leaders()


class Project(TimestampedModel):
    """A project is a collection of runs done by the same team"""

    class Status(Enum):
        TO_SCHEDULE = 1, _("To schedule")
        SCHEDULED = 11, _("Scheduled")
        ONGOING = 21, _("Ongoing")
        FINISHED = 31, _("Finished")
        DATA_AVAILABLE = 41, _("Data uploaded")

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
            "Mark this project as confidential. "
            "This will hide it from external servicecs (Euphrosyne Diglab, ...)."
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

    comments = models.TextField(_("Description"), blank=True)

    is_data_available = models.BooleanField(
        _("Data available"),
        default=False,
        help_text=_("Has at least one run with data available."),
    )

    # For optimization, when queryset is created with with_prefetched_leaders
    # manager method, this attribute will be populated with the leader participation
    prefetched_leaders: QuerySet[Participation]

    def __str__(self):
        return f"{self.name}"

    @property
    def leader(self) -> Optional["Participation"]:
        """Get the leader participation for this project.

        This property uses one of two methods to retrieve the leader:
        1. If the project was loaded with Project.objects.with_prefetched_leaders(),
           it will use the prefetched data (most efficient)
        2. Otherwise, it will execute a database query (less efficient)

        For optimal performance in admin interfaces or list views, use:
        `Project.objects.with_prefetched_leaders()` to load projects.

        Returns:
            The Participation object for the project leader, or None if no leader exists
        """
        # First check if we have prefetched leaders
        if (
            # pylint: disable=no-member
            hasattr(self, "prefetched_leaders")
            and self.prefetched_leaders
        ):
            return self.prefetched_leaders[0]  # pylint: disable=no-member

        # Fall back to database query
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
            if any(
                run["start_date"] and timezone.now() > run["start_date"]
                for run in runs_with_start_date
            ):
                return self.Status.ONGOING
            return self.Status.SCHEDULED
        return self.Status.TO_SCHEDULE

    status.fget.short_description = _("Status")  # type: ignore

    def clean(self):
        super().clean()
        if not self.name:
            raise ValidationError(
                {"name": ValidationError(_("Project name cannot be empty."))}
            )
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
                            "and another project with this slug exists."
                        )
                        % slug
                    )
                }
            )

    def save(self, *args, **kwargs) -> None:
        self.slug = self._generate_slug()
        return super().save(*args, **kwargs)

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
