from datetime import time
from typing import Any, Mapping

from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.base import File
from django.db.models.base import Model
from django.forms.fields import BooleanField, EmailField, SplitDateTimeField
from django.forms.forms import Form
from django.forms.models import ModelForm
from django.forms.utils import ErrorList
from django.forms.widgets import HiddenInput, Select
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from euphro_auth.models import User, UserInvitation

from . import models, widgets
from .controlled_datalist import controlled_datalist_form
from .emails import send_project_invitation_email
from .methods import OTHER_VALUE, SelectWithFreeOther


class BaseParticipationForm(ModelForm):
    user = EmailField(label=_("User"))

    def __init__(
        self, initial=None, instance: models.Participation = None, **kwargs
    ) -> None:
        if instance:
            initial = {**(initial or {}), "user": instance.user.email}
        super().__init__(initial=initial, instance=instance, **kwargs)
        self.fields["user"].widget.attrs["placeholder"] = _("Email")
        if instance:
            self.fields["institution"].widget.instance = instance.institution

    def try_populate_institution(self):
        if not self.data.get(f"{self.prefix}-institution") and self.data.get(
            f"{self.prefix}-institution__name"
        ):
            (
                institution,
                _,
            ) = models.Institution.objects.get_or_create(
                name=self.data[f"{self.prefix}-institution__name"],
                country=self.data.get(f"{self.prefix}-institution__country"),
                ror_id=self.data.get(f"{self.prefix}-institution__ror_id"),
            )
            self.data[f"{self.prefix}-institution"] = institution.pk

    def clean(self) -> dict[str, Any]:
        cleaned_data = super().clean()
        if "user" in cleaned_data:
            # Try to find user with email, create it otherwise
            try:
                user = get_user_model().objects.get(email=cleaned_data["user"])
            except get_user_model().DoesNotExist:
                user = UserInvitation.create_user(email=cleaned_data["user"])
            return {**cleaned_data, "user": user}
        return cleaned_data

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
        widgets = {"institution": widgets.InstitutionAutoCompleteWidget()}
        labels = {"institution": _("Institution")}


class LeaderParticipationForm(BaseParticipationForm):
    """Participation model form that automatically set `is_leader` to
    `True` when saving the instance.
    """

    is_leader = forms.BooleanField(widget=HiddenInput(), initial=True)

    class Meta:
        model = models.Participation
        fields = ("user", "institution")
        widgets = {
            "institution": widgets.InstitutionWidgetWrapper(
                Select(), models.Institution.participation_set.rel
            ),
        }

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.fields["user"].label = _("Leader")

    def save(self, commit: bool = ...) -> models.Participation:
        super().save(commit=False)
        self.instance.is_leader = True
        self.instance.save()
        self._save_m2m()


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


RECOMMENDED_ENERGY_LEVELS = {
    models.Run.ParticleType.PROTON: [1000, 1500, 2000, 2500, 3000, 3500, 3800, 4000],
    models.Run.ParticleType.ALPHA: [3000, 4000, 5000, 6000],
    models.Run.ParticleType.DEUTON: [1000, 1500, 2000],
}


def _get_energy_levels_choices(
    particle_type: str,
) -> list[tuple[str, str]]:
    return [(level, level) for level in RECOMMENDED_ENERGY_LEVELS[particle_type]]


class BaseRunDetailsForm(ModelForm):
    class Meta:
        model = models.Run
        fields = []

        widgets = {
            **{
                filter_fieldname: (
                    Select(choices=[(c, c) for c in ["", *choices]])
                    if OTHER_VALUE not in choices
                    else SelectWithFreeOther(choices=[(c, c) for c in ["", *choices]])
                )
                for filter_fieldname, choices in [
                    (field.name, field.filters)
                    for field in models.Run.get_filters_fields()
                ]
            },
        }

    def clean(self):
        cleaned_data = super().clean()
        errors = {}

        cleaned_data, errors = self._clean_methods(cleaned_data, errors)

        if errors:
            raise ValidationError(errors)
        return cleaned_data

    def _clean_methods(self, cleaned_data, errors):
        # Reset detectors whose method is not selected:
        for method_field, detector_field in models.Run.get_method_detector_fields():
            if not cleaned_data.get(method_field.name):
                cleaned_data[detector_field.name] = (
                    False
                    if isinstance(self.fields[detector_field.name], BooleanField)
                    else ""
                )
        for (
            method_field,
            detector_field,
            filters_field,
        ) in models.Run.get_method_detector_filters_fields():
            # Reset filter whose detector is not selected:
            if not cleaned_data.get(detector_field.name):
                cleaned_data[filters_field.name] = ""
            # Validate filter choice if no freeform allowed
            if (
                cleaned_data.get(filters_field.name)
                and cleaned_data[filters_field.name] not in filters_field.filters
                and OTHER_VALUE not in filters_field.filters
            ):
                errors[filters_field.name] = ValidationError(
                    _("Invalid filter choice"), code="invalid-filters-choice"
                )
        return cleaned_data, errors


@controlled_datalist_form(
    controller_field_name="particle_type",
    controlled_field_name="energy_in_keV",
    choices={
        particle_type: _get_energy_levels_choices(particle_type)
        for particle_type in models.Run.ParticleType
    },
)
class RunDetailsForm(BaseRunDetailsForm):
    class Meta(BaseRunDetailsForm.Meta):
        fields = (
            "beamline",
            *[f.name for f in models.Run.get_method_fields()],
            *[f.name for f in models.Run.get_detector_fields()],
            *[f.name for f in models.Run.get_filters_fields()],
        )


@controlled_datalist_form(
    controller_field_name="particle_type",
    controlled_field_name="energy_in_keV",
    choices={
        particle_type: _get_energy_levels_choices(particle_type)
        for particle_type in models.Run.ParticleType
    },
)
class RunDetailsAdminForm(BaseRunDetailsForm):
    class Meta(BaseRunDetailsForm.Meta):
        fields = fields = (
            "label",
            "beamline",
            *[f.name for f in models.Run.get_method_fields()],
            *[f.name for f in models.Run.get_detector_fields()],
            *[f.name for f in models.Run.get_filters_fields()],
        )


class RunCreateForm(ModelForm):
    class Meta:
        model = models.Run
        fields = ("label",)

    def save(self, commit: bool = False) -> Any:
        self.instance.embargo_date = timezone.now() + timezone.timedelta(days=365 * 2)
        return super().save(commit)


class RunCreateAdminForm(ModelForm):
    class Meta:
        model = models.Run
        fields = ("label", "embargo_date")

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        data: Mapping[str, Any] | None = None,
        files: Mapping[str, File] | None = None,
        auto_id: bool | str = "id_%s",
        prefix: str | None = None,
        initial: dict[str, Any] | None = None,
        error_class: ErrorList = ErrorList,
        label_suffix: str | None = None,
        empty_permitted: bool = False,
        instance: Model | None = None,
        use_required_attribute: bool | None = None,
        renderer: Any = None,
    ):
        if not initial:
            initial = {}
        initial["embargo_date"] = timezone.now() + timezone.timedelta(days=365 * 2)
        super().__init__(
            data,
            files,
            auto_id,
            prefix,
            initial,
            error_class,
            label_suffix,
            empty_permitted,
            instance,
            use_required_attribute,
            renderer,
        )


class RunStatusBaseForm(ModelForm):
    MANDATORY_FIELDS = ("label", "start_date", "end_date", "beamline")

    class Meta:
        model = models.Run
        fields = ("status",)

    def _clean_status_not_new_mandatory_fields(self, cleaned_status):
        if cleaned_status and cleaned_status != models.Run.Status.NEW:
            missing_fields = [
                rf for rf in self.MANDATORY_FIELDS if not getattr(self.instance, rf)
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

    def _clean_status_not_new_1_method_required(self, cleaned_status):
        if cleaned_status and cleaned_status != models.Run.Status.NEW:
            if all(
                not getattr(self.instance, f.name)
                for f in models.Run.get_method_fields()
            ):
                raise ValidationError(
                    _("The run can't start while no method is selected."),
                    code="ask_exec_not_allowed_if_no_method",
                )

    def clean(self):
        cleaned_data = super().clean()
        cleaned_status = cleaned_data.get("status")

        self._clean_status_not_new_mandatory_fields(cleaned_status)
        self._clean_status_not_new_1_method_required(cleaned_status)

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


class RunScheduleForm(ModelForm):
    start_date = SplitDateTimeField(
        widget=widgets.SplitDateTimeWithDefaultTime(default_time_value=time(9)),
    )
    end_date = SplitDateTimeField(
        widget=widgets.SplitDateTimeWithDefaultTime(default_time_value=time(18)),
    )

    class Meta:
        model = models.Run
        fields = ("start_date", "end_date", "embargo_date")

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        data: Mapping[str, Any] | None = None,
        files: Mapping[str, File] | None = None,
        auto_id: bool | str = "id_%s",
        prefix: str | None = None,
        initial: dict[str, Any] | None = None,
        error_class: ErrorList = ErrorList,
        label_suffix: str | None = None,
        empty_permitted: bool = False,
        instance: Model | None = None,
        use_required_attribute: bool | None = None,
        renderer: Any = None,
    ) -> None:
        if not initial:
            initial = {}
        if (
            not instance or not instance.embargo_date
        ) and "embargo_date" not in initial:
            initial["embargo_date"] = timezone.now() + timezone.timedelta(days=365 * 2)
        super().__init__(
            data,
            files,
            auto_id,
            prefix,
            initial,
            error_class,
            label_suffix,
            empty_permitted,
            instance,
            use_required_attribute,
            renderer,
        )
        self.fields["embargo_date"].widget.format = "%Y-%m-%d"
        self.fields["embargo_date"].widget.input_type = "date"

    def clean(self):
        cleaned_data = super().clean()
        errors = {}

        cleaned_data, errors = self._clean_dates(cleaned_data, errors)

        if errors:
            raise ValidationError(errors)
        return cleaned_data

    @staticmethod
    def _clean_dates(cleaned_data, errors):
        cleaned_start_date = cleaned_data.get("start_date")
        cleaned_end_date = cleaned_data.get("end_date")

        if (
            cleaned_start_date
            and cleaned_end_date
            and cleaned_end_date < cleaned_start_date
        ):
            errors["end_date"] = ValidationError(
                _("The end date must be after the start date"),
                code="start_date_after_end_date",
            )

        return cleaned_data, errors


class BeamTimeRequestForm(ModelForm):
    class Meta:
        model = models.BeamTimeRequest
        fields = ("request_type", "request_id", "form_type", "problem_statement")
        widgets = {"problem_statement": widgets.CounterTextarea()}


class ProjectForm(ModelForm):
    has_accepted_cgu = forms.BooleanField(
        required=True,
        label=_("I have read and accepted the general conditions of Euphrosyne."),
    )

    class Meta:
        model = models.Project
        fields = ["name", "confidential"]
