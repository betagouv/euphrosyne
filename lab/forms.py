import enum
from typing import Any, Dict, Mapping

from django import forms
from django.core.exceptions import ValidationError
from django.forms.fields import BooleanField
from django.forms.forms import Form
from django.forms.models import ModelForm
from django.forms.utils import ErrorList
from django.forms.widgets import HiddenInput, Select
from django.utils.translation import gettext_lazy as _

from euphro_auth.models import User
from lab.emails import send_project_invitation_email
from lab.models.run import ObjectGroup

from . import models, widgets
from .controlled_datalist import controlled_datalist_form
from .methods import OTHER_VALUE, SelectWithFreeOther


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
        labels = {"user": _("User"), "institution": _("Institution")}


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


RECOMMENDED_ENERGY_LEVELS = {
    models.Run.ParticleType.PROTON: [1000, 1500, 2000, 2500, 3000, 3500, 3800, 4000],
    models.Run.ParticleType.ALPHA: [3000, 4000, 5000, 6000],
    models.Run.ParticleType.DEUTON: [1000, 1500, 2000],
}


def _get_energy_levels_choices(
    particle_type: str,
) -> list[tuple[str, str]]:
    return [(level, level) for level in RECOMMENDED_ENERGY_LEVELS[particle_type]]


@controlled_datalist_form(
    controller_field_name="particle_type",
    controlled_field_name="energy_in_keV",
    choices={
        particle_type: _get_energy_levels_choices(particle_type)
        for particle_type in models.Run.ParticleType
    },
)
class RunDetailsForm(ModelForm):
    class Meta:
        model = models.Run
        fields = (
            "label",
            "start_date",
            "end_date",
            "beamline",
            *[f.name for f in models.Run.get_method_fields()],
            *[f.name for f in models.Run.get_detector_fields()],
            *[f.name for f in models.Run.get_filters_fields()],
        )

        widgets = {
            "project": widgets.ProjectWidgetWrapper(
                widgets.DisabledSelectWithHidden(),
                models.Run.project.field.remote_field,  # pylint: disable=no-member
            ),
            **{
                filter_fieldname: Select(choices=[(c, c) for c in ["", *choices]])
                if OTHER_VALUE not in choices
                else SelectWithFreeOther(choices=[(c, c) for c in ["", *choices]])
                for filter_fieldname, choices in [
                    (field.name, field.filters)
                    for field in models.Run.get_filters_fields()
                ]
            },
        }

    def clean(self):
        cleaned_data = super().clean()
        errors = {}

        cleaned_data, errors = self._clean_dates(cleaned_data, errors)
        cleaned_data, errors = self._clean_methods(cleaned_data, errors)

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


class ObjectGroupAddChoices(enum.Enum):
    OBJECT_GROUP = "OBJECT_GROUP", _("Group of objects")
    SINGLE_OBJECT = "SINGLE_OBJECT", _("One object")

    @classmethod
    def to_choices(cls):
        return (choice.value for choice in cls)


class ObjectGroupForm(forms.ModelForm):
    add_type = forms.ChoiceField(
        label="",
        choices=ObjectGroupAddChoices.to_choices(),
        widget=widgets.ChoiceTag(),
    )

    class Meta:
        model = ObjectGroup
        fields = ("add_type", "label", "materials", "dating", "inventory", "collection")
        help_texts = {"materials": _("Separate each material with a comma")}
        widgets = {"materials": widgets.TagsInput()}

    def __init__(self, *args, **kwargs: Mapping[str, Any]) -> None:
        super().__init__(*args, **kwargs)
        if self.instance.id:
            self.fields["add_type"].required = False
            self.fields["add_type"].widget.attrs["disabled"] = "disabled"
            self.fields["add_type"].initial = (
                ObjectGroupAddChoices.OBJECT_GROUP.value[0]
                if self.instance.object_set.count() > 1
                else ObjectGroupAddChoices.SINGLE_OBJECT.value[0]
            )
            if self.instance.object_set.count() == 1:
                self.fields["label"].widget = forms.HiddenInput()
        else:
            self.fields["add_type"].initial = ObjectGroupAddChoices.OBJECT_GROUP.value[
                0
            ]

    def clean(self) -> Dict[str, Any]:
        cleaned_data = super().clean()
        add_type = cleaned_data.get("add_type")
        if add_type == ObjectGroupAddChoices.OBJECT_GROUP.value[
            0
        ] and not cleaned_data.get("label"):
            raise ValidationError(
                {
                    "label": ValidationError(
                        _(
                            "Group label must be specified "
                            "when adding multiple objects"
                        ),
                        code="label-required-for-mulitple-objects",
                    )
                }
            )
        return cleaned_data


class BeamTimeRequestForm(ModelForm):
    class Meta:
        model = models.BeamTimeRequest
        fields = ("request_type", "request_id", "form_type", "problem_statement")
        widgets = {"problem_statement": widgets.CounterTextarea()}
