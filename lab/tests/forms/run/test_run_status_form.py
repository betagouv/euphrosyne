import pytest

from .... import forms, models
from ... import factories


def test_new_run_requires_no_field():
    form = forms.RunStatusBaseForm(data={"status": models.Run.Status.CREATED.value})
    assert form.is_valid()


@pytest.mark.parametrize(
    "status",
    [s.value for s in models.Run.Status if s != models.Run.Status.CREATED.value],
)
def test_status_can_move_after_new_if_fields_are_defined(status):
    form = forms.RunStatusBaseForm(
        instance=factories.RunReadyToAskExecFactory.build(),
        data={"status": status},
    )
    assert form.is_valid()


@pytest.mark.parametrize(
    "mandatory_field", ["label", "start_date", "end_date", "beamline"]
)
@pytest.mark.parametrize(
    "status",
    [s.value for s in models.Run.Status if s != models.Run.Status.CREATED.value],
)
def test_not_new_requires_mandatory_field_to_be_defined(status, mandatory_field):
    form = forms.RunStatusBaseForm(
        instance=factories.RunReadyToAskExecFactory.build(**{mandatory_field: None}),
        data={"status": status},
    )
    assert form.has_error("__all__", code="missing_field_for_run_start")


@pytest.mark.parametrize(
    "status",
    [
        s.value
        for s in models.Run.Status
        if s
        not in [
            models.Run.Status.ASK_FOR_EXECUTION.value,
            models.Run.Status.CREATED.value,
        ]
    ],
)
def test_member_cant_do_more_than_ask_for_execution(status):
    form = forms.RunStatusMemberForm(data={"status": status})
    assert form.has_error("status", code="run_execution_not_allowed_to_members")


@pytest.mark.parametrize(
    "status",
    [
        s.value
        for s in models.Run.Status
        if s
        not in [
            models.Run.Status.ASK_FOR_EXECUTION.value,
            models.Run.Status.CREATED.value,
        ]
    ],
)
def test_member_cant_change_status_if_planned_or_more(status):
    form = forms.RunStatusMemberForm(
        instance=models.Run(status=status),
        data={"status": models.Run.Status.ASK_FOR_EXECUTION.value},
    )
    assert form.has_error("status", code="run_rewinding_not_allowed_to_members")


@pytest.mark.parametrize("method_field", models.Run.get_method_fields())
def test_one_method_selected_allows_for_ask_exec(method_field):
    run = factories.RunForceNoMethodFactory.build(
        **{"status": models.Run.Status.CREATED.value}
    )
    setattr(run, method_field.name, True)
    form = forms.RunStatusMemberForm(
        instance=run,
        data={"status": models.Run.Status.ASK_FOR_EXECUTION.value},
    )
    assert form.is_valid()


def test_no_method_selected_does_not_allow_for_ask_exec():
    form = forms.RunStatusMemberForm(
        instance=factories.RunForceNoMethodFactory.build(
            status=models.Run.Status.CREATED.value
        ),
        data={"status": models.Run.Status.ASK_FOR_EXECUTION.value},
    )
    assert form.has_error("__all__", code="ask_exec_not_allowed_if_no_method")
