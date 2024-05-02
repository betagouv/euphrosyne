from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from lab.methods import MethodModel
from lab.validators import valid_filename
from shared.models import TimestampedModel


class RunManager(models.Manager):
    def only_finished(self):
        return super().get_queryset().filter(end_date__lt=timezone.now())


class Run(TimestampedModel, MethodModel):
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["label", "project"], name="label_project_unique"
            )
        ]

    class Status(models.IntegerChoices):
        CREATED = 1, _("Created")
        ASK_FOR_EXECUTION = 11, _("Ask for execution")
        ONGOING = 21, _("Ongoing")
        FINISHED = 31, _("Finished")

    class ParticleType(models.TextChoices):
        PROTON = "Proton", _("Proton")
        ALPHA = "Alpha particle", _("Alpha particle")
        DEUTON = "Deuton", _("Deuton")

    objects = RunManager()

    project = models.ForeignKey(
        "lab.Project",
        null=False,
        on_delete=models.PROTECT,
        related_name="runs",
        verbose_name=_("Project"),
    )
    label = models.CharField(
        _("Run label"), max_length=255, validators=[valid_filename]
    )

    status = models.IntegerField(
        _("Run status"),
        choices=Status.choices,
        default=Status.CREATED,
    )

    start_date = models.DateTimeField(_("Start date"), null=True, blank=True)
    end_date = models.DateTimeField(_("End date"), null=True, blank=True)
    embargo_date = models.DateField(_("Embargo date"), null=True, blank=True)

    particle_type = models.CharField(
        _("Particle type"), max_length=45, choices=ParticleType.choices, blank=True
    )
    energy_in_keV = models.IntegerField(
        _("Energy level (in keV)"), null=True, blank=True
    )

    class Beamline(models.TextChoices):
        MICROBEAM = "Microbeam", _("Microbeam")

    beamline = models.CharField(
        _("Beamline"),
        max_length=45,
        choices=Beamline.choices,
        default=Beamline.MICROBEAM,
    )

    run_object_groups = models.ManyToManyField(
        "lab.ObjectGroup", verbose_name=_("Object groups"), related_name="runs"
    )

    def __str__(self):
        return self.label

    def next_status(self) -> Status:
        if self.status is None:
            return list(Run.Status)[0]
        idx = Run.Status.values.index(self.status)
        try:
            next_status = list(Run.Status)[idx + 1]
        except IndexError as exception:
            raise AttributeError("Run has no next status") from exception
        return next_status
