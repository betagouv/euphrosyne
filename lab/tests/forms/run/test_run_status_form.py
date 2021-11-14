import pytest

from .... import forms, models


def test_new_requires_no_fields():
    form = forms.RunStatusBaseForm(data={"status": models.Run.Status.NEW})
    assert form.is_valid()


@pytest.mark.parametrize(
    "status",
    [s for s in models.Run.Status if s != models.Run.Status.NEW],
)
def test_not_new_requires_instance_to_be_filled(status):
    form = forms.RunStatusBaseForm(instance=models.Run(), data={"status": status})
    assert form.has_error("__all__", code="missing_field_for_run_start")


@pytest.mark.parametrize(
    "status",
    [
        s
        for s in models.Run.Status
        if s not in [models.Run.Status.ASK_FOR_EXECUTION, models.Run.Status.NEW]
    ],
)
def test_member_cant_do_more_than_ask_for_execution(status):
    form = forms.RunStatusMemberForm(data={"status": status})
    assert form.has_error("status", code="run_execution_not_allowed_to_members")


@pytest.mark.parametrize(
    "status",
    [
        s
        for s in models.Run.Status
        if s not in [models.Run.Status.ASK_FOR_EXECUTION, models.Run.Status.NEW]
    ],
)
def test_member_cant_change_status_if_planned_or_more(status):
    form = forms.RunStatusMemberForm(
        instance=models.Run(status=status),
        data={"status": models.Run.Status.ASK_FOR_EXECUTION},
    )
    assert form.has_error("status", code="run_rewinding_not_allowed_to_members")
