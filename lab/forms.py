from pathlib import Path
from typing import List, Tuple

import yaml
from django import forms
from django.core.exceptions import ValidationError
from django.forms.forms import Form
from django.forms.models import ModelForm
from django.forms.utils import ErrorList
from django.forms.widgets import HiddenInput, Select
from django.utils.translation import gettext_lazy as _

from euphro_auth.models import User
from lab.emails import send_project_invitation_email

from . import models, widgets
from .controlled_datalist import controlled_datalist_form

# [TODO] Rewrite
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


# [XXX] Replace this by RunDetailsForm._meta.fields
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


def _get_energy_levels_choices(
    particle_type: str,
) -> List[Tuple[str, str]]:
    return [
        (level, f"{level} keV") for level in RECOMMENDED_ENERGY_LEVELS[particle_type]
    ]


@controlled_datalist_form(
    controller_field_name="particle_type",
    controlled_field_name="energy_in_keV",
    choices={
        particle_type: _get_energy_levels_choices(particle_type)
        for particle_type in models.Run.ParticleType
    },
    controller_verbose_name=_("Particle type"),
)
class RunDetailsForm(ModelForm):
    class Meta:
        model = models.Run
        fields = tuple(
            set(RUN_DETAILS_FIELDS) - set(("particle_type", "energy_in_keV"))
        )
        widgets = {
            "project": widgets.ProjectWidgetWrapper(
                widgets.DisabledSelectWithHidden(),
                models.Run.project.field.remote_field,  # pylint: disable=no-member
            )
        }

    def clean(self):
        cleaned_data = super().clean()
        cleaned_start_date = cleaned_data.get("start_date")
        cleaned_end_date = cleaned_data.get("end_date")
        cleaned_embargo_date = cleaned_data.get("embargo_date")

        errors = {}

        if (
            cleaned_start_date
            and cleaned_end_date
            and cleaned_end_date < cleaned_start_date
        ):
            errors["end_date"] = ValidationError(
                _("The end date must be after the start date"),
                code="start_date_after_end_date",
            )

        if (
            cleaned_end_date
            and cleaned_embargo_date
            and cleaned_embargo_date < cleaned_end_date.date()
        ):
            errors["embargo_date"] = ValidationError(
                _("The embargo date must be after the end date"),
                code="end_date_after_embargo_date",
            )
        if errors:
            raise ValidationError(errors)
        return cleaned_data


class RunStatusBaseForm(ModelForm):
    class Meta:
        model = models.Run
        fields = ("status",)

    def clean(self):
        cleaned_data = super().clean()
        cleaned_status = cleaned_data.get("status")

        if cleaned_status and cleaned_status != models.Run.Status.NEW:
            missing_fields = [
                rf for rf in RUN_DETAILS_FIELDS if not getattr(self.instance, rf)
            ]
            missing_fields_verbose = [
                str(_(models.Run._meta.get_field(field_name).verbose_name))
                for field_name in missing_fields
            ]
            if missing_fields:
                raise ValidationError(
                    _(
                        "The run can't start while the following Run fields aren't "
                        "defined: {fields}."
                    ).format(fields=", ".join(missing_fields_verbose)),
                    code="missing_field_for_run_start",
                )

        return cleaned_data


class RunStatusAdminForm(RunStatusBaseForm):
    pass


class RunStatusMemberForm(RunStatusBaseForm):
    def clean_status(self):
        status = self.cleaned_data["status"]
        if status not in [
            models.Run.Status.NEW,
            models.Run.Status.ASK_FOR_EXECUTION,
        ]:
            raise ValidationError(
                _("Only Admin users might validate and execute runs."),
                code="run_execution_not_allowed_to_members",
            )
        if self.instance and self.instance.status not in [
            models.Run.Status.NEW,
            models.Run.Status.ASK_FOR_EXECUTION,
        ]:

            raise ValidationError(
                _("Only Admin users might rewind runs."),
                code="run_rewinding_not_allowed_to_members",
            )
        return status
