from pathlib import Path

import yaml
from django import forms
from django.contrib.admin import site as admin_site
from django.contrib.admin.widgets import RelatedFieldWidgetWrapper
from django.core.exceptions import ValidationError
from django.forms.forms import Form
from django.forms.models import ModelForm
from django.forms.utils import ErrorList
from django.forms.widgets import HiddenInput, Select
from django.utils.translation import gettext_lazy as _

from euphro_auth.models import User
from lab.emails import send_project_invitation_email

from . import models, widgets

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
                # [XXX] Bug: plus button still appears
                can_add_related=False,
                can_change_related=False,
                can_delete_related=True,
                can_view_related=False,
            )
        }

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

    def clean_status(self):
        status = self.cleaned_data["status"]

        if status != models.Run.Status.NOT_STARTED:
            # All fields must be defined to start the run.
            self._validate_all_fields_are_defined_to_start()
            # [XXX] Launch validation of existence of analysis technique and
            # nested objects on status change.
            # An analysis technique must be selected for the run to start.
            self._validate_analysis_technique_exists_to_start()

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
