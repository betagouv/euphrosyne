from pathlib import Path

import yaml
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from shared.models import TimestampedModel

with open(Path(__file__).parent / "run-choices-config.yaml") as f:
    RUN_CHOICES = yaml.safe_load(f.read())


class Run(TimestampedModel):
    class Status(models.TextChoices):
        NOT_STARTED = "Not started", _("Not started")
        ASK_FOR_EXECUTION = "Ask for execution", _("Ask for execution")
        STARTED = "Started", _("Started")
        FINISHED = "Finished", _("Finished")

    class ParticleType(models.TextChoices):
        PROTON = "Proton"
        ALPHA = "Alpha particle", _("Alpha particle")
        DEUTON = "Deuton"

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
        default=Status.NOT_STARTED,
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

    def __str__(self):
        return self.label


class AnalysisTechniqueUsed(models.Model):
    # Choices will need to be removed here and managed into forms as soon as
    # there will be more than one beamline.
    MICROBEAM_ANALYSIS_TECHNIQUES = list(
        RUN_CHOICES["beamlines"]["Microbeam"]["analysis_techniques"].keys()
    )

    run = models.ForeignKey(
        Run,
        null=False,
        on_delete=models.CASCADE,
        related_name="analysis_techniques_used",
    )

    label = models.CharField(
        _("Label"),
        max_length=45,
        choices=zip(MICROBEAM_ANALYSIS_TECHNIQUES, MICROBEAM_ANALYSIS_TECHNIQUES),
        blank=False,
    )

    def __str__(self):
        return _("{analysis_technique_label} used in {run}").format(
            analysis_technique_label=self.label, run=self.run
        )


class DetectorUsed(models.Model):
    analysis_technique_used = models.ForeignKey(
        AnalysisTechniqueUsed,
        null=False,
        on_delete=models.CASCADE,
        related_name="detectors_used",
    )

    label = models.CharField(_("Label"), max_length=45, blank=False)

    detector_filter = models.CharField(_("Filter"), max_length=45, blank=True)

    def __str__(self):
        return _(
            "{detector_label} with filter {detector_filter} with "
            "{analysis_technique_used}"
        ).format(
            detector_label=self.label,
            detector_filter=self.detector_filter,
            analysis_technique_used=self.analysis_technique_used,
        )
