from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.translation import gettext_lazy as _

from shared.models import TimestampedModel

from ..methods import MethodModel


class Run(TimestampedModel, MethodModel):
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
    label = models.CharField(_("Run label"), max_length=255, unique=True)

    status = models.CharField(
        _("Run status"),
        max_length=45,
        choices=Status.choices,
        default=Status.NEW,
    )

    start_date = models.DateTimeField(_("Run start of period"), null=True, blank=True)
    end_date = models.DateTimeField(_("Run end of period"), null=True, blank=True)
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


class ObjectGroup(models.Model):
    label = models.CharField(
        _("Group label"),
        max_length=255,
        blank=True,
    )
    inventory = models.CharField(
        _("Inventory"),
        max_length=255,
        blank=True,
    )
    dating = models.CharField(
        _("Dating"),
        max_length=255,
    )
    materials = ArrayField(
        models.CharField(max_length=255),
        verbose_name=_("Materials"),
        default=list,
    )
    discovery_place = models.CharField(
        _("Place of discovery"),
        max_length=255,
        blank=True,
    )
    collection = models.CharField(
        _("Collection"),
        max_length=255,
        blank=True,
    )

    def __str__(self) -> str:
        label = (
            self.object_set.first().label
            if self.object_set.count() == 1
            else f"(Group) {self.label}"
        )
        materials = ", ".join(self.materials)

        return f"{label} - {self.dating} - {materials}"


class Object(models.Model):
    group = models.ForeignKey(ObjectGroup, on_delete=models.CASCADE)
    label = models.CharField(_("Label"), max_length=255)
    differentiation_information = models.CharField(
        _("Differentiation information"), max_length=255, blank=True
    )
