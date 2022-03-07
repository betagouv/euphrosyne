from django.contrib.postgres.fields import ArrayField
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from shared.models import TimestampedModel

from ..methods import MethodModel


class Run(TimestampedModel, MethodModel):
    class Status(models.IntegerChoices):
        CREATED = 1, _("Created")
        ASK_FOR_EXECUTION = 11, _("Ask for execution")
        ONGOING = 21, _("Ongoing")
        FINISHED = 31, _("Finished")

    class ParticleType(models.TextChoices):
        PROTON = "Proton", _("Proton")
        ALPHA = "Alpha particle", _("Alpha particle")
        DEUTON = "Deuton", _("Deuton")

    project = models.ForeignKey(
        "lab.Project", null=False, on_delete=models.PROTECT, related_name="runs"
    )
    label = models.CharField(_("Run label"), max_length=255, unique=True)

    status = models.IntegerField(
        _("Run status"),
        choices=Status.choices,
        default=Status.CREATED,
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

    def next_status(self) -> Status:
        if self.status is None:
            return list(Run.Status)[0]
        idx = Run.Status.values.index(self.status)
        try:
            next_status = list(Run.Status)[idx + 1]
        except IndexError as exception:
            raise AttributeError("Run has no next status") from exception
        return next_status


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

    class Meta:
        verbose_name = _("Batch of objects")
        verbose_name_plural = _("Batches of objects")


class Object(models.Model):
    group = models.ForeignKey(ObjectGroup, on_delete=models.CASCADE)
    label = models.CharField(_("Label"), max_length=255)
    differentiation_information = models.CharField(
        _("Differentiation information"),
        max_length=255,
        blank=True,
    )
    inventory = models.CharField(
        _("Inventory"),
        max_length=255,
        blank=True,
    )
    collection = models.CharField(
        _("Collection"),
        max_length=255,
        blank=True,
    )
    total_number = models.IntegerField(
        _("Total number"),
        null=True,
        blank=True,
        help_text=_("Number of objects if more than one"),
        validators=[MinValueValidator(1)],
    )
