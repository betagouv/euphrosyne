import datetime
from datetime import time
from typing import Any, Mapping

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from django.db.models.base import Model
from django.forms.fields import BooleanField, SplitDateTimeField
from django.forms.models import ModelForm
from django.forms.utils import ErrorList
from django.forms.widgets import Select
from django.utils import timezone
from django.utils.datastructures import MultiValueDict
from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy as _

from lab import widgets
from lab.methods import OTHER_VALUE, SelectWithFreeOther

from . import models


class BaseRunDetailsForm(ModelForm):
    class Meta:
        model = models.Run
        fields: list[str] = []

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


class RunDetailsForm(BaseRunDetailsForm):
    class Meta(BaseRunDetailsForm.Meta):
        fields = [
            "beamline",
            *[f.name for f in models.Run.get_method_fields()],
            *[f.name for f in models.Run.get_detector_fields()],
            *[f.name for f in models.Run.get_filters_fields()],
        ]


class RunDetailsAdminForm(BaseRunDetailsForm):
    class Meta(BaseRunDetailsForm.Meta):
        fields = [
            "label",
            "beamline",
            *[f.name for f in models.Run.get_method_fields()],
            *[f.name for f in models.Run.get_detector_fields()],
            *[f.name for f in models.Run.get_filters_fields()],
        ]


def get_run_details_form_class():
    return import_string(
        getattr(settings, "RUN_DETAILS_FORM_CLASS", "lab.runs.forms.RunDetailsForm")
    )


def get_run_details_admin_form_class():
    return import_string(
        getattr(
            settings,
            "RUN_DETAILS_ADMIN_FORM_CLASS",
            "lab.runs.forms.RunDetailsAdminForm",
        )
    )


class RunCreateForm(ModelForm):
    class Meta:
        model = models.Run
        fields = ("label",)

    def save(self, commit: bool = False) -> Any:
        self.instance.embargo_date = timezone.now() + datetime.timedelta(days=365 * 2)
        return super().save(commit)


class RunCreateAdminForm(ModelForm):
    class Meta:
        model = models.Run
        fields = ("label", "embargo_date")

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        data: Mapping[str, Any] | None = None,
        files: MultiValueDict[str, UploadedFile] | None = None,
        auto_id: bool | str = "id_%s",
        prefix: str | None = None,
        initial: dict[str, Any] | None = None,
        error_class: type[ErrorList] = ErrorList,
        label_suffix: str | None = None,
        empty_permitted: bool = False,
        instance: Model | None = None,
        use_required_attribute: bool | None = None,
        renderer: Any = None,
    ):
        if not initial:
            initial = {}
        initial["embargo_date"] = timezone.now() + datetime.timedelta(days=365 * 2)
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

    permanent_embargo = BooleanField(
        label=_("Permanent embargo"), required=False, label_suffix=""
    )

    class Meta:
        model = models.Run
        fields = ("start_date", "end_date", "embargo_date")

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        data: Mapping[str, Any] | None = None,
        files: MultiValueDict[str, UploadedFile] | None = None,
        auto_id: bool | str = "id_%s",
        prefix: str | None = None,
        initial: dict[str, Any] | None = None,
        error_class: type[ErrorList] = ErrorList,
        label_suffix: str | None = None,
        empty_permitted: bool = False,
        instance: models.Run | None = None,
        use_required_attribute: bool | None = None,
        renderer: Any = None,
    ) -> None:
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
        if (
            instance
            and instance.embargo_date is None
            and "embargo_date" not in (data or {})
        ):
            self.fields["permanent_embargo"].initial = True
        # on POST, if embargo_date is not set, set it to None
        # as it means permanent embargo is checked
        if data and "embargo_date" not in data:
            self.instance.embargo_date = None

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
