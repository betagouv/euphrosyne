from pathlib import Path

import yaml
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from shared.models import TimestampedModel

with open(Path(__file__).parent / "run-choices-config.yaml") as f:
    RUN_CHOICES = yaml.safe_load(f.read())


class Run(TimestampedModel):
    class RunStatuses(models.TextChoices):
        NOT_STARTED = "Not started", _("Not started")
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
        choices=RunStatuses.choices,
        default=RunStatuses.NOT_STARTED,
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
        return _("run {run_label}").format(run_label=self.label)

    def clean(self):
        if self.status != self.RunStatuses.NOT_STARTED:
            required_fields_at_start = set(f.name for f in self._meta.get_fields())
            missing_fields = [
                rf for rf in required_fields_at_start if not getattr(self, rf)
            ]
            # All fields must be defined to start the run.
            if missing_fields:
                raise ValidationError(
                    {
                        missing_field: _(
                            "The run can't start while this field isn't defined."
                        )
                        for missing_field in missing_fields
                    }
                )
            beamline_choices = RUN_CHOICES["beamlines"][self.beamline]
            # An analysis technique must be selected for the run to start.
            if (
                beamline_choices.get("analysis_techniques", None)
                and not self.analysis_techniques_used.exists()
            ):
                raise ValidationError(
                    _(
                        "The beamline {beamline} requires an analysis technique to be "
                        "defined."
                    ).format(beamline=self.beamline)
                )


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

    def clean(self):
        beamline = self.run.beamline
        analysis_techniques_available = RUN_CHOICES["beamlines"][beamline].get(
            "analysis_techniques", dict()
        )
        # Analysis technique must correspond to beamline.
        if self.label not in analysis_techniques_available.keys():
            raise ValidationError(
                _(
                    "The analysis technique in use ({label}) doesn't correspond to "
                    "the instrument's beamline in use ({beamline})"
                ).format(label=self.label, beamline=self.run.beamline)
            )
        analysis_technique_choices = analysis_techniques_available[self.label]
        # There must be a detector used for an analysis technique which has
        # available detector choices.
        if (
            analysis_technique_choices.get("detectors", None)
            and not self.detectors_used.exists()
        ):
            raise ValidationError(
                _(
                    "Analysis technique {analysis_technique_label} requires a detector."
                ).format(analysis_technique_label=self.label)
            )

    def __str__(self):
        return _("technique {analysis_technique_label} in run {run}").format(
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

    def clean(self):
        run = self.analysis_technique_used.run
        analysis_technique_label = self.analysis_technique_used.label
        detectors_available = RUN_CHOICES["beamlines"][run.beamline][
            "analysis_techniques"
        ][analysis_technique_label].get("detectors", dict())
        detector_label = self.label
        detector_filter = self.detector_filter
        # Detector must correspond to analysis technique used.
        if detector_label and detector_label not in detectors_available.keys():
            raise ValidationError(
                _(
                    "The detector used ({detector_label}) doesn't correspond to "
                    "the analysis technique in use ({analysis_technique_label})"
                ).format(
                    detector_label=self.label,
                    analysis_technique_label=analysis_technique_label,
                )
            )
        detector_choices = detectors_available[detector_label]
        # There must be a filter used for a detector which has available filter
        # choices, and the filter must correspond to the detector used.
        if (
            detector_choices.get("filters", None)
            and detector_filter not in detector_choices["filters"]
        ):
            if not detector_filter:
                raise ValidationError(
                    _("The detector used ({detector_label}) requires a filter.").format(
                        detector_label=detector_label
                    )
                )
            raise ValidationError(
                _(
                    "The detector filter used ({detector_filter}) doesn't correspond "
                    "to the detector used ({detector_label})"
                ).format(detector_filter=detector_filter, detector_label=detector_label)
            )

    def __str__(self):
        return _(
            "detector {detector_label} with filter {detector_filter} in "
            "{analysis_technique_used}"
        ).format(
            detector_label=self.label,
            detector_filter=self.detector_filter,
            analysis_technique_used=self.analysis_technique_used,
        )
