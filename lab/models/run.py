from django.db import models
from django.utils.translation import gettext_lazy as _

from shared.models import TimestampedModel

from ..methods import MethodModel


class Run(TimestampedModel, MethodModel):
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["label", "project"], name="label_project_unique"
            )
        ]

    class Status(models.TextChoices):
        NEW = "New", _("New")
        ASK_FOR_EXECUTION = "Ask for execution", _("Ask for execution")
        PLANNED = "Planned", _("Planned")
        STARTED = "Started", _("Started")
        FINISHED = "Finished", _("Finished")

    class ParticleType(models.TextChoices):
        PROTON = "Proton", _("Proton")
        ALPHA = "Alpha particle", _("Alpha particle")
        DEUTON = "Deuton", _("Deuton")

    project = models.ForeignKey(
        "lab.Project", null=False, on_delete=models.PROTECT, related_name="runs"
    )
    label = models.CharField(_("Run label"), max_length=255)

    status = models.CharField(
        _("Run status"),
        max_length=45,
        choices=Status.choices,
        default=Status.NEW,
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
