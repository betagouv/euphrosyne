from pathlib import Path

import yaml
from django.db import models
from django.utils.translation import gettext_lazy as _

from shared.models import TimestampedModel

with open(Path(__file__).parent / "run-choices-config.yaml") as f:
    RUN_CHOICES = yaml.safe_load(f.read())


class Run(TimestampedModel):
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

    BEAMLINE_NAMES = {
        beam_label: beam_choices["name"]
        for beam_label, beam_choices in RUN_CHOICES["beamlines"].items()
    }

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

    beamline = models.CharField(
        _("Beamline"), max_length=45, choices=BEAMLINE_NAMES.items(), blank=True
    )

    methods = models.JSONField(null=True)

    def __str__(self):
        return self.label
