from datetime import timedelta
from typing import Any

import pytest
from django.utils import timezone

from data_management.models import (
    LifecycleOperation,
    LifecycleOperationStatus,
    LifecycleOperationType,
    LifecycleState,
    ProjectData,
)
from lab.tests.factories import ProjectFactory


def create_operation(
    project_data: ProjectData,
    operation_type: LifecycleOperationType,
    **overrides: Any,
) -> LifecycleOperation:
    data = {
        "project_data": project_data,
        "type": operation_type,
        "status": LifecycleOperationStatus.SUCCEEDED,
        "bytes_copied": project_data.project_size_bytes,
        "files_copied": project_data.file_count,
    }
    data.update(overrides)
    return LifecycleOperation.objects.create(**data)


def create_project_data(**overrides: Any) -> ProjectData:
    project = overrides.pop("project", None) or ProjectFactory()
    project_data = ProjectData.for_project(project)
    for key, value in overrides.items():
        setattr(project_data, key, value)
    if overrides:
        project_data.save(update_fields=list(overrides.keys()))
    return project_data


@pytest.mark.django_db
def test_for_project_backfills_missing_cooling_eligible_at():
    project = ProjectFactory()
    project_data = ProjectData.for_project(project)
    expected = project_data.cooling_eligible_at

    project_data.cooling_eligible_at = None
    project_data.save(update_fields=["cooling_eligible_at"])

    reloaded = ProjectData.for_project(project)

    assert reloaded.cooling_eligible_at == expected


@pytest.mark.django_db
def test_last_lifecycle_operation_ignores_null_timestamps():
    project = ProjectFactory()
    project_data = create_project_data(project=project)

    LifecycleOperation.objects.create(
        project_data=project_data,
        type=LifecycleOperationType.COOL,
        status=LifecycleOperationStatus.PENDING,
    )

    base_time = timezone.now()
    LifecycleOperation.objects.create(
        project_data=project_data,
        type=LifecycleOperationType.COOL,
        status=LifecycleOperationStatus.RUNNING,
        started_at=base_time - timedelta(hours=1),
    )  # running
    finished = LifecycleOperation.objects.create(
        project_data=project_data,
        type=LifecycleOperationType.RESTORE,
        status=LifecycleOperationStatus.SUCCEEDED,
        finished_at=base_time,
    )

    assert project_data.last_lifecycle_operation == finished


@pytest.mark.django_db
def test_last_lifecycle_operation_prefers_started_over_pending():
    project = ProjectFactory()
    project_data = create_project_data(project=project)

    LifecycleOperation.objects.create(
        project_data=project_data,
        type=LifecycleOperationType.COOL,
        status=LifecycleOperationStatus.PENDING,
    )

    running = LifecycleOperation.objects.create(
        project_data=project_data,
        type=LifecycleOperationType.COOL,
        status=LifecycleOperationStatus.RUNNING,
        started_at=timezone.now(),
    )

    assert project_data.last_lifecycle_operation == running


@pytest.mark.django_db
def test_transition_to_cooling_requires_hot_and_eligible():
    eligible_project_data = create_project_data(
        cooling_eligible_at=timezone.now() - timedelta(days=1),
    )

    eligible_project_data.transition_to(LifecycleState.COOLING)

    assert eligible_project_data.lifecycle_state == LifecycleState.COOLING

    not_eligible_project_data = create_project_data(
        cooling_eligible_at=timezone.now() + timedelta(days=1),
    )

    with pytest.raises(ValueError):
        not_eligible_project_data.transition_to(LifecycleState.COOLING)

    not_hot_project_data = create_project_data(
        lifecycle_state=LifecycleState.COOL,
        cooling_eligible_at=timezone.now() - timedelta(days=1),
    )

    with pytest.raises(ValueError):
        not_hot_project_data.transition_to(LifecycleState.COOLING)


@pytest.mark.django_db
def test_transition_to_cool_requires_succeeded_operation_and_verification():
    project_data = create_project_data(
        lifecycle_state=LifecycleState.COOLING,
        project_size_bytes=10,
        file_count=2,
    )
    operation = create_operation(project_data, LifecycleOperationType.COOL)

    project_data.transition_to(LifecycleState.COOL, operation=operation)

    assert project_data.lifecycle_state == LifecycleState.COOL


@pytest.mark.django_db
@pytest.mark.parametrize(
    "overrides",
    [
        {"status": LifecycleOperationStatus.FAILED},
        {"type": LifecycleOperationType.RESTORE},
        {"bytes_copied": 9},
        {"files_copied": 1},
        {"bytes_copied": None},
    ],
)
def test_transition_to_cool_rejects_invalid_operation(overrides):
    project_data = create_project_data(
        lifecycle_state=LifecycleState.COOLING,
        project_size_bytes=10,
        file_count=2,
    )
    operation = create_operation(project_data, LifecycleOperationType.COOL)
    for key, value in overrides.items():
        setattr(operation, key, value)
    operation.save()

    with pytest.raises(ValueError):
        project_data.transition_to(LifecycleState.COOL, operation=operation)


@pytest.mark.django_db
def test_transition_to_cool_rejects_missing_operation_or_expected_totals():
    project_data = create_project_data(
        lifecycle_state=LifecycleState.COOLING,
        project_size_bytes=10,
        file_count=2,
    )

    with pytest.raises(ValueError):
        project_data.transition_to(LifecycleState.COOL, operation=None)

    project_data = create_project_data(
        lifecycle_state=LifecycleState.COOLING,
        project_size_bytes=None,
        file_count=2,
    )
    operation = create_operation(
        project_data, LifecycleOperationType.COOL, bytes_copied=10
    )

    with pytest.raises(ValueError):
        project_data.transition_to(LifecycleState.COOL, operation=operation)


@pytest.mark.django_db
def test_transition_to_cool_rejects_operation_from_other_project_data():
    project_data = create_project_data(
        lifecycle_state=LifecycleState.COOLING,
        project_size_bytes=10,
        file_count=2,
    )
    other_project_data = create_project_data(
        lifecycle_state=LifecycleState.COOLING,
        project_size_bytes=10,
        file_count=2,
    )
    operation = create_operation(other_project_data, LifecycleOperationType.COOL)

    with pytest.raises(ValueError):
        project_data.transition_to(LifecycleState.COOL, operation=operation)


@pytest.mark.django_db
def test_transition_to_restoring_requires_cool():
    project_data = create_project_data(
        lifecycle_state=LifecycleState.COOL,
    )

    project_data.transition_to(LifecycleState.RESTORING)

    assert project_data.lifecycle_state == LifecycleState.RESTORING

    not_cool_project_data = create_project_data(
        lifecycle_state=LifecycleState.HOT,
    )

    with pytest.raises(ValueError):
        not_cool_project_data.transition_to(LifecycleState.RESTORING)


@pytest.mark.django_db
def test_transition_to_hot_requires_succeeded_operation_and_verification():
    project_data = create_project_data(
        lifecycle_state=LifecycleState.RESTORING,
        project_size_bytes=10,
        file_count=2,
    )
    operation = create_operation(project_data, LifecycleOperationType.RESTORE)

    project_data.transition_to(LifecycleState.HOT, operation=operation)

    assert project_data.lifecycle_state == LifecycleState.HOT


@pytest.mark.django_db
@pytest.mark.parametrize(
    "overrides",
    [
        {"status": LifecycleOperationStatus.FAILED},
        {"type": LifecycleOperationType.COOL},
        {"bytes_copied": 9},
        {"files_copied": 1},
        {"files_copied": None},
    ],
)
def test_transition_to_hot_rejects_invalid_operation(overrides):
    project_data = create_project_data(
        lifecycle_state=LifecycleState.RESTORING,
        project_size_bytes=10,
        file_count=2,
    )
    operation = create_operation(project_data, LifecycleOperationType.RESTORE)
    for key, value in overrides.items():
        setattr(operation, key, value)
    operation.save()

    with pytest.raises(ValueError):
        project_data.transition_to(LifecycleState.HOT, operation=operation)


@pytest.mark.django_db
def test_transition_to_hot_rejects_operation_from_other_project_data():
    project_data = create_project_data(
        lifecycle_state=LifecycleState.RESTORING,
        project_size_bytes=10,
        file_count=2,
    )
    other_project_data = create_project_data(
        lifecycle_state=LifecycleState.RESTORING,
        project_size_bytes=10,
        file_count=2,
    )
    operation = create_operation(other_project_data, LifecycleOperationType.RESTORE)

    with pytest.raises(ValueError):
        project_data.transition_to(LifecycleState.HOT, operation=operation)


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("state", "allowed"),
    [
        (LifecycleState.COOLING, True),
        (LifecycleState.RESTORING, True),
        (LifecycleState.HOT, False),
        (LifecycleState.COOL, False),
    ],
)
def test_transition_to_error_only_from_operation_states(state, allowed):
    project_data = create_project_data(lifecycle_state=state)

    if allowed:
        project_data.transition_to(LifecycleState.ERROR)
        assert project_data.lifecycle_state == LifecycleState.ERROR
    else:
        with pytest.raises(ValueError):
            project_data.transition_to(LifecycleState.ERROR)
