from io import StringIO
from unittest import mock

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from data_management.models import (
    LifecycleOperation,
    LifecycleOperationStatus,
    LifecycleOperationType,
    LifecycleState,
)

from .factories import ProjectDataFactory


@pytest.mark.django_db
def test_cool_project_dispatches_hot_project():
    project_data = ProjectDataFactory()

    with mock.patch(
        "data_management.management.commands.cool_project._dispatch_cooling_operation",
        return_value=True,
    ) as dispatch_mock:
        call_command("cool_project", project_data.project.slug, stdout=StringIO())

    operation = LifecycleOperation.objects.get()

    assert dispatch_mock.call_count == 1
    dispatched_project_data, dispatched_operation = dispatch_mock.call_args.args
    assert dispatched_project_data.pk == project_data.pk
    assert dispatched_operation.pk == operation.pk
    assert operation.project_data_id == project_data.pk
    assert operation.type == LifecycleOperationType.COOL
    assert operation.status == LifecycleOperationStatus.RUNNING


@pytest.mark.django_db
def test_cool_project_rejects_error_project_without_dispatch():
    project_data = ProjectDataFactory(lifecycle_state=LifecycleState.ERROR)

    with mock.patch(
        "data_management.management.commands.cool_project._dispatch_cooling_operation"
    ) as dispatch_mock:
        with pytest.raises(
            CommandError,
            match="does not exist or is not currently HOT",
        ):
            call_command("cool_project", project_data.project.slug, stdout=StringIO())

    assert dispatch_mock.call_count == 0
    assert LifecycleOperation.objects.count() == 0
