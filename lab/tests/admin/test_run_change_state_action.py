# pylint: disable=redefined-outer-name
# pylint: disable=no-member
from unittest import mock

import pytest
from django.contrib.admin.sites import AdminSite
from django.core.exceptions import ValidationError

# from django.db.models import QuerySet
from django.test.client import RequestFactory
from django.urls import reverse

from ...admin import run_actions
from ...admin.run import RunAdmin
from ...models import Run
from .. import factories


@pytest.fixture
def modeladmin():
    return RunAdmin(model=Run, admin_site=AdminSite())


@pytest.fixture
def changelist_request():
    return RequestFactory().get(reverse("admin:lab_run_changelist"))


@mock.patch.object(run_actions, "validate_mandatory_fields", mock.Mock())
@mock.patch.object(run_actions, "validate_1_method_required", mock.Mock())
@mock.patch.object(run_actions, "validate_not_last_state", mock.Mock())
@mock.patch.object(run_actions, "validate_execute_needs_admin", mock.Mock())
@mock.patch.object(run_actions, "send_message", mock.Mock())
@mock.patch.object(run_actions, "change_status", mock.Mock())
def test_change_state_calls_validators_and_changes_status(
    modeladmin, changelist_request
):
    queryset = [Run()]
    changelist_request.user = None

    run_actions.change_state(modeladmin, changelist_request, queryset)

    run_actions.validate_mandatory_fields.assert_called_once()
    run_actions.validate_1_method_required.assert_called_once()
    run_actions.validate_not_last_state.assert_called_once()
    run_actions.validate_execute_needs_admin.assert_called_once()
    run_actions.change_status.assert_called_once()


@mock.patch.object(run_actions, "validate_mandatory_fields", mock.Mock())
@mock.patch.object(run_actions, "validate_1_method_required", mock.Mock())
@mock.patch.object(run_actions, "validate_not_last_state", mock.Mock())
@mock.patch.object(
    run_actions,
    "validate_execute_needs_admin",
    mock.Mock(side_effect=ValidationError("test")),
)
@mock.patch.object(run_actions, "send_message", mock.Mock())
@mock.patch.object(run_actions, "change_status", mock.Mock())
def test_change_state_class_message(modeladmin, changelist_request):
    queryset = [Run()]
    changelist_request.user = None

    run_actions.change_state(modeladmin, changelist_request, queryset)

    run_actions.send_message.assert_called_with(changelist_request, "test", "error")


@pytest.mark.parametrize(
    "status",
    [s for s in Run.Status if s != Run.Status.FINISHED],
)
def test_not_last_state_can_change(status):
    run = factories.RunReadyToAskExecFactory.build(status=status)

    run_actions.validate_not_last_state(run)


def test_last_state_can_change():
    run = factories.RunReadyToAskExecFactory.build(status=Run.Status.FINISHED)

    with pytest.raises(ValidationError):
        run_actions.validate_not_last_state(run)


@pytest.mark.parametrize(
    "status",
    [s for s in Run.Status if s != Run.Status.FINISHED],
)
def test_status_can_move_after_new_if_fields_are_defined(status):
    run = factories.RunReadyToAskExecFactory.build(status=status)

    run_actions.validate_mandatory_fields(run)


@pytest.mark.parametrize("mandatory_field", run_actions.MANDATORY_FIELDS)
@pytest.mark.parametrize(
    "status",
    [s for s in Run.Status if s != Run.Status.FINISHED],
)
def test_not_new_requires_mandatory_field_to_be_defined(status, mandatory_field):
    run = factories.RunReadyToAskExecFactory.build(
        **{"status": status, mandatory_field: None}
    )

    with pytest.raises(ValidationError):
        run_actions.validate_mandatory_fields(run)


@pytest.mark.parametrize("method_field", Run.get_method_fields())
def test_one_method_selected_allows_for_ask_exec(method_field):
    run = factories.RunFactory.build(
        **{"status": Run.Status.CREATED, method_field.name: True}
    )

    run_actions.validate_1_method_required(run)


def test_no_method_selected_does_not_allow_for_ask_exec():
    run = factories.RunForceNoMethodFactory.build(**{"status": Run.Status.CREATED})

    with pytest.raises(ValidationError):
        run_actions.validate_1_method_required(run)


def test_member_can_ask_for_execution():
    run = factories.RunFactory.build(status=Run.Status.CREATED)
    user = factories.StaffUserFactory.build()

    run_actions.validate_execute_needs_admin(user, run)


@pytest.mark.parametrize(
    "status",
    [s for s in Run.Status if s != Run.Status.FINISHED],
)
def test_admin_can_change_state(status):
    run = factories.RunFactory.build(status=status)
    user = factories.LabAdminUserFactory.build()

    run_actions.validate_execute_needs_admin(user, run)


@pytest.mark.parametrize(
    "status",
    [s for s in Run.Status if s != Run.Status.CREATED],
)
def test_member_cant_do_more_than_ask_for_execution(status):
    run = factories.RunFactory.build(status=status)
    user = factories.StaffUserFactory.build()

    with pytest.raises(ValidationError):
        run_actions.validate_execute_needs_admin(user, run)
