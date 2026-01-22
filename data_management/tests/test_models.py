from datetime import timedelta

import pytest
from django.utils import timezone

from data_management.models import (
    LifecycleOperation,
    LifecycleOperationStatus,
    LifecycleOperationType,
    RunData,
)
from lab.tests.factories import RunFactory


@pytest.mark.django_db
def test_last_lifecycle_operation_ignores_null_timestamps():
    run = RunFactory()
    run_data = RunData.objects.create(run=run)

    LifecycleOperation.objects.create(
        project_run_data=run_data,
        type=LifecycleOperationType.COOL,
        status=LifecycleOperationStatus.PENDING,
    )

    base_time = timezone.now()
    running = LifecycleOperation.objects.create(
        project_run_data=run_data,
        type=LifecycleOperationType.COOL,
        status=LifecycleOperationStatus.RUNNING,
        started_at=base_time - timedelta(hours=1),
    )
    finished = LifecycleOperation.objects.create(
        project_run_data=run_data,
        type=LifecycleOperationType.RESTORE,
        status=LifecycleOperationStatus.SUCCEEDED,
        finished_at=base_time,
    )

    assert run_data.last_lifecycle_operation == finished


@pytest.mark.django_db
def test_last_lifecycle_operation_prefers_started_over_pending():
    run = RunFactory()
    run_data = RunData.objects.create(run=run)

    LifecycleOperation.objects.create(
        project_run_data=run_data,
        type=LifecycleOperationType.COOL,
        status=LifecycleOperationStatus.PENDING,
    )

    running = LifecycleOperation.objects.create(
        project_run_data=run_data,
        type=LifecycleOperationType.COOL,
        status=LifecycleOperationStatus.RUNNING,
        started_at=timezone.now(),
    )

    assert run_data.last_lifecycle_operation == running
