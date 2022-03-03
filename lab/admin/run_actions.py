from typing import Optional

from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from euphro_auth.models import User

from ..models import Run
from ..permissions import is_lab_admin

MANDATORY_FIELDS = ("label", "start_date", "end_date", "beamline")


def validate_mandatory_fields(run: Run):
    missing_fields = [rf for rf in MANDATORY_FIELDS if not getattr(run, rf)]
    missing_fields_verbose = [
        str(_(Run._meta.get_field(field_name).verbose_name))
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


def validate_1_method_required(run: Run):
    if all(not getattr(run, f.name) for f in Run.get_method_fields()):
        raise ValidationError(
            _("The run can't start while no method is selected."),
            code="ask_exec_not_allowed_if_no_method",
        )


def validate_not_last_state(run: Run):
    if run.status == Run.Status.FINISHED:
        raise ValidationError(_("Impossible to change the state of a finished Run"))


def validate_execute_needs_admin(user: User, run: Run):
    if not is_lab_admin(user) and run.status != Run.Status.CREATED:
        raise ValidationError(
            _("Only Admin users might validate and execute runs."),
            code="run_execution_not_allowed_to_members",
        )


def send_message(request, message: str):
    messages.error(request, message)


@admin.action(description=_("Change state"))
def change_state(modeladmin, request, queryset):
    """Change state forward"""
    try:
        for run in queryset:
            validate_not_last_state(run)
            validate_mandatory_fields(run)
            validate_1_method_required(run)
            validate_execute_needs_admin(request.user, run)
    except ValidationError as e:
        send_message(request, e.message)


def get_change_state_text(labadmin: bool, run: Run) -> Optional[str]:
    return {
        Run.Status.CREATED: _("Ask for execution"),
        Run.Status.ASK_FOR_EXECUTION: _("Start Run") if labadmin else None,
        Run.Status.ONGOING: _("Finish Run") if labadmin else None,
        Run.Status.FINISHED: None,
    }[run.status]
