from django.db import models
from django.utils.translation import gettext_lazy as _

from lab.runs.metadata.models import RunMetadataModel


class EuphrosyneRunMetadataModel(RunMetadataModel):
    """
    Concrete implementation of RunMetadataModel for the AGLAE laboratory.
    This model defines the actual database fields for run metadata.
    """

    class Meta:
        app_label = "euphrosyne"
        abstract = True

    class ParticleType(models.TextChoices):
        PROTON = "Proton", _("Proton")
        ALPHA = "Alpha particle", _("Alpha particle")
        DEUTON = "Deuton", _("Deuton")

    class Beamline(models.TextChoices):
        MICROBEAM = "Microbeam", _("Microbeam")

    particle_type = models.CharField(
        _("Particle type"), max_length=45, choices=ParticleType.choices, blank=True
    )
    energy_in_keV = models.IntegerField(
        _("Energy level (in keV)"), null=True, blank=True
    )
    beamline = models.CharField(
        _("Beamline"),
        max_length=45,
        choices=Beamline.choices,
        default=Beamline.MICROBEAM,
    )

    @classmethod
    def get_experimental_condition_fieldset_fields(cls):
        return [
            "particle_type",
            "energy_in_keV",
            "beamline",
        ]
