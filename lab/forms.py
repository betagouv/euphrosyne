from pathlib import Path
from typing import List, Optional, Tuple

import yaml
from django import forms
from django.contrib.admin import site as admin_site
from django.contrib.admin.widgets import RelatedFieldWidgetWrapper
from django.core.exceptions import ValidationError
from django.forms.forms import Form
from django.forms.models import ModelForm
from django.forms.utils import ErrorList
from django.forms.widgets import HiddenInput, Select, TextInput
from django.utils.translation import gettext_lazy as _

from euphro_auth.models import User
from lab.emails import send_project_invitation_email

from . import fields, models, widgets

# [XXX] Wrap in a service
with open(Path(__file__).parent / "models" / "run-choices-config.yaml") as f:
    RUN_CHOICES = yaml.safe_load(f.read())


class BaseParticipationForm(ModelForm):
    def save(self, commit: bool = ...) -> models.Participation:
        is_new = self.instance.pk is None
        instance = super().save(commit=commit)
        if is_new:
            user: User = instance.user
            send_project_invitation_email(
                email=user.email,
                project=instance.project,
            )
        return instance

    class Meta:
        model = models.Participation
        fields = ("user", "institution")
        widgets = {
            "user": widgets.UserWidgetWrapper(
                Select(),
                User.participation_set.rel,
            ),
            "institution": widgets.InstitutionWidgetWrapper(
                Select(), models.Institution.participation_set.rel
            ),
        }


class LeaderParticipationForm(BaseParticipationForm):
    """Participation model form that automatically set `is_leader` to
    `True` when saving the instance.
    """

    is_leader = forms.BooleanField(widget=HiddenInput(), initial=True)

    class Meta:
        model = models.Participation
        fields = ("user", "institution")
        widgets = {
            "user": widgets.UserWidgetWrapper(
                Select(),
                User.participation_set.rel,
            ),
            "institution": widgets.InstitutionWidgetWrapper(
                Select(), models.Institution.participation_set.rel
            ),
        }
        labels = {
            "user": _("Leader"),
        }

    def save(self, commit: bool = ...) -> models.Participation:
        self.instance.is_leader = True
        return super().save(commit=commit)


class ChangeLeaderForm(Form):

    leader_participation = forms.ModelChoiceField(
        queryset=None, empty_label=_("No leader"), label=_("Leader")
    )

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        project: models.Project,
        data=None,
        files=None,
        auto_id="id_%s",
        prefix=None,
        initial=None,
        error_class=ErrorList,
        label_suffix=None,
        empty_permitted=False,
        field_order=None,
        use_required_attribute=None,
        renderer=None,
    ) -> None:
        initial = {"leader_participation": project.leader}
        super().__init__(
            data=data,
            files=files,
            auto_id=auto_id,
            prefix=prefix,
            initial=initial,
            error_class=error_class,
            label_suffix=label_suffix,
            empty_permitted=empty_permitted,
            field_order=field_order,
            use_required_attribute=use_required_attribute,
            renderer=renderer,
        )
        self.fields["leader_participation"].queryset = project.participation_set


RUN_DETAILS_FIELDS = (
    "label",
    "start_date",
    "end_date",
    "embargo_date",
    "particle_type",
    "energy_in_keV",
    "beamline",
)

RECOMMENDED_ENERGY_LEVELS = {
    models.Run.ParticleType.PROTON: [1000, 1500, 2000, 2500, 3000, 3500, 3800, 4000],
    models.Run.ParticleType.ALPHA: [3000, 4000, 5000, 6000],
    models.Run.ParticleType.DEUTON: [1000, 1500, 2000],
}


def get_energy_levels_choices(
    particle_type: str,
) -> List[Tuple[str, str]]:
    return [
        (level, f"{level} keV") for level in RECOMMENDED_ENERGY_LEVELS[particle_type]
    ]


# [XXX] Run end > run start and embargo >= run end
class RunDetailsForm(ModelForm):
    class Meta:
        model = models.Run
        fields = RUN_DETAILS_FIELDS
        widgets = {
            "project": RelatedFieldWidgetWrapper(
                widgets.DisabledSelectWithHidden(),
                models.Run.project.field.remote_field,  # pylint: disable=no-member
                admin_site,
                # [FIXME] Bug: plus button still appears
                can_add_related=False,
                can_change_related=False,
                can_delete_related=True,
                can_view_related=False,
            ),
        }

    energy_in_keV = fields.MultiDatalistIntegerField(
        widget=widgets.MultiDatalistWidget(
            control_field_name="particle_type",
            widgets={
                particle_type: widgets.ControlledDatalist(
                    field_name="energy_in_keV",
                    control_value=particle_type,
                    choices=get_energy_levels_choices(particle_type),
                )
                for particle_type in models.Run.ParticleType
            },
        ),
    )

    # Note: this validation will be useful when we will have multiple beamlines.
    def clean_beamline(self):
        beamline = self.cleaned_data["beamline"]
        if beamline not in RUN_CHOICES["beamlines"].keys():
            raise ValidationError(
                _("Available beamlines are %(beamlines)s"),
                params={"beamlines": ", ".join(RUN_CHOICES["beamlines"].keys())},
                code="invalid_beamline",
            )
        return beamline

    def clean(self):
        cleaned_data = super().clean()
        # Get the right energy level depending on particle_type
        energies = cleaned_data.get("energy_in_keV")
        particle_type = cleaned_data.get("particle_type")
        if not particle_type:
            cleaned_data["energy_in_keV"] = None
        else:
            # [XXX] Test that order is kept from PaticleTypes to energies
            cleaned_data["energy_in_keV"] = energies[
                list(models.Run.ParticleType).index(particle_type)
            ]
        return cleaned_data


class RunStatusBaseForm(ModelForm):
    class Meta:
        model = models.Run
        fields = ("status",)

    def _validate_all_fields_are_defined_to_start(self):
        missing_fields = [
            rf for rf in RUN_DETAILS_FIELDS if not getattr(self.instance, rf)
        ]
        if missing_fields:
            raise ValidationError(
                {
                    missing_field: _(
                        "The run can't start while this field isn't defined."
                    )
                    for missing_field in missing_fields
                },
                code="missing_field_for_run_start",
            )

    def _validate_analysis_technique_exists_to_start(self):
        beamline = self.instance.beamline
        beamline_choices = RUN_CHOICES["beamlines"][beamline]
        if (
            beamline_choices.get("analysis_techniques")
            and not self.instance.analysis_techniques_used.exists()
        ):
            raise ValidationError(
                _(
                    "The beamline %(beamline)s requires at least an analysis "
                    "technique to be used. Please define one before launching "
                    "the run."
                ),
                params={"beamline": beamline},
                code="no_analysis_technique_used_on_run_start",
            )

    def _validate_detectors_exist_to_start(self):
        analysis_techniques_available = RUN_CHOICES["beamlines"][
            self.instance.beamline
        ].get("analysis_techniques", dict())
        analysis_techniques_used = self.instance.analysis_technique_used.all()
        errors = []
        for analysis_technique_used in analysis_techniques_used:
            analysis_technique_choices = analysis_techniques_available[
                analysis_technique_used.label
            ]
            if (
                analysis_technique_choices.get("detectors", None)
                and not analysis_technique_used.detectors_used.exists()
            ):
                errors += _(
                    "Analysis technique {analysis_technique_label} requires a detector."
                ).format(analysis_technique_label=analysis_technique_used.label)
        if errors:
            raise ValidationError(
                "\n".join(errors), code="no_detector_used_for_some_analysis_techniques"
            )

    def clean_status(self):
        status = self.cleaned_data["status"]

        if status != models.Run.Status.NOT_STARTED:
            # All fields must be defined to start the run.
            self._validate_all_fields_are_defined_to_start()
            # An analysis technique must be selected for the run to start.
            self._validate_analysis_technique_exists_to_start()
            # A detector must be used for any analysis technique which has
            # available detector choices.
            self._validate_detectors_exist_to_start()

        return status


class RunStatusAdminForm(RunStatusBaseForm):
    pass


class RunStatusParticipantForm(RunStatusBaseForm):
    def clean_status(self):
        status = super().clean_status()
        if status not in [
            models.Run.Status.NOT_STARTED,
            models.Run.Status.ASK_FOR_EXECUTION,
        ]:
            raise ValidationError(
                _("Only Admin users might start or stop the execution."),
                code="run_execution_not_allowed_for_participants",
            )
        return status


class AnalysisTechniqueUsedAdminForm(ModelForm):
    class Meta:
        model = models.AnalysisTechniqueUsed
        fields = "__all__"
        widgets = {
            "run": RelatedFieldWidgetWrapper(
                widgets.DisabledSelectWithHidden(),
                models.AnalysisTechniqueUsed.run.field.remote_field,  # pylint: disable=no-member
                admin_site,
                # [FIXME] Bug: plus button still appears
                can_add_related=False,
                can_change_related=False,
                can_delete_related=True,
                can_view_related=False,
            ),
        }

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("run"):
            run = cleaned_data["run"]
            beamline = run.beamline
            if beamline:
                analysis_techniques_available = RUN_CHOICES["beamlines"][beamline].get(
                    "analysis_techniques", dict()
                )
                label = cleaned_data.get("label")
                # Analysis technique must correspond to beamline.
                if label not in analysis_techniques_available.keys():
                    raise ValidationError(
                        _(
                            "The analysis technique in use ({label}) doesn't "
                            "correspond to the instrument's beamline in use "
                            "({beamline})."
                        ).format(label=label, beamline=beamline),
                        code="analysis_technique_used_incoherent_with_beamline",
                    )


def build_detector_used_inline_form(choices: Optional[List[str]] = None):
    class DetectorUsedInlineForm(ModelForm):
        class Meta:
            model = models.DetectorUsed
            fields = "__all__"
            widgets = {
                "label": Select(choices=zip(choices, choices))
                if choices
                else TextInput()
            }

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            import pdb

            pdb.set_trace()

        def clean(self):
            cleaned_data = super().clean()
            label = cleaned_data.get("label")
            detector_filter = cleaned_data.get("detector_filter")

            analysis_technique_used = cleaned_data["analysis_technique_used"]
            analysis_technique_label = analysis_technique_used.label
            run = analysis_technique_used.run

            if run.beamline and analysis_technique_label:
                detectors_available = RUN_CHOICES["beamlines"][run.beamline][
                    "analysis_techniques"
                ][analysis_technique_label].get("detectors", dict())
                # Detector must correspond to analysis technique used.
                if label and label not in detectors_available.keys():
                    raise ValidationError(
                        _(
                            "The detector used ({label}) doesn't correspond to "
                            "the analysis technique in use ({analysis_technique_label})"
                        ).format(
                            label=label,
                            analysis_technique_label=analysis_technique_label,
                        ),
                        code="detector_used_incoherent_with_analysis_technique",
                    )

                detector_choices = detectors_available[label]
                # There must be a filter used for a detector which has available filter
                # choices, and the filter must correspond to the detector used.
                if (
                    detector_choices.get("filters", None)
                    and detector_filter not in detector_choices["filters"]
                ):
                    if not detector_filter:
                        raise ValidationError(
                            _(
                                "The detector used ({detector_label}) requires "
                                "a filter."
                            ).format(label=label),
                            code="detector_filter_required",
                        )
                    raise ValidationError(
                        _(
                            "The detector filter used ({detector_filter}) doesn't "
                            "correspond to the detector used ({detector_label})"
                        ).format(detector_filter=detector_filter, label=label),
                        code="detector_filter_incoherent_with_detector",
                    )

    return DetectorUsedInlineForm
