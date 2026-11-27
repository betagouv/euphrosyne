"""Reconcile lifecycle operations that never received a completion callback.

The tools API runs COOL/RESTORE copies in a background task and tracks them in
memory only. If the worker dies mid-copy (deploy, restart, out-of-memory), no
callback ever reaches Euphrosyne: the operation stays ``RUNNING`` and the
project stays in ``COOLING`` / ``RESTORING`` forever, with no retry possible.

``fail_stale_lifecycle_operations`` marks such operations ``FAILED`` and moves
the project to ``ERROR`` so the usual retry path becomes available again.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .models import (
    LifecycleOperation,
    LifecycleOperationStatus,
    LifecycleOperationType,
    LifecycleState,
    ProjectData,
)

logger = logging.getLogger(__name__)

DEFAULT_STALE_AFTER_HOURS = 6

# Project state expected while an operation of a given type is in flight.
_IN_FLIGHT_STATE_BY_TYPE: dict[str, LifecycleState] = {
    LifecycleOperationType.COOL: LifecycleState.COOLING,
    LifecycleOperationType.RESTORE: LifecycleState.RESTORING,
}


@dataclass(frozen=True)
class StaleOperation:
    operation_id: str
    project_slug: str
    type: str
    started_at: datetime | None
    project_moved_to_error: bool


def get_stale_after() -> timedelta:
    hours = getattr(
        settings, "DATA_LIFECYCLE_OPERATION_TIMEOUT_HOURS", DEFAULT_STALE_AFTER_HOURS
    )
    return timedelta(hours=hours)


def fail_stale_lifecycle_operations(
    *,
    stale_after: timedelta | None = None,
    dry_run: bool = False,
    now: datetime | None = None,
) -> list[StaleOperation]:
    """Fail PENDING/RUNNING operations started more than ``stale_after`` ago.

    Returns the operations that were (or, with ``dry_run``, would be) failed.
    A late callback from the tools API is ignored afterwards, because the
    callback endpoint no-ops on operations already in a terminal status.
    """
    now = now or timezone.now()
    stale_after = stale_after or get_stale_after()
    cutoff = now - stale_after

    candidate_ids = list(
        LifecycleOperation.objects.filter(
            status__in=[
                LifecycleOperationStatus.PENDING,
                LifecycleOperationStatus.RUNNING,
            ],
            started_at__lt=cutoff,
        ).values_list("operation_id", flat=True)
    )

    results: list[StaleOperation] = []
    for operation_id in candidate_ids:
        result = _fail_operation(
            operation_id,
            stale_after=stale_after,
            now=now,
            dry_run=dry_run,
        )
        if result is not None:
            results.append(result)
    return results


def _fail_operation(
    operation_id,
    *,
    stale_after: timedelta,
    now: datetime,
    dry_run: bool,
) -> StaleOperation | None:
    with transaction.atomic():
        project_data = (
            ProjectData.objects.select_for_update()
            .select_related("project")
            .filter(lifecycle_operations__operation_id=operation_id)
            .first()
        )
        if project_data is None:
            return None
        operation = LifecycleOperation.objects.select_for_update().get(
            operation_id=operation_id
        )
        # A callback may have completed the operation since the candidate query.
        if operation.status not in (
            LifecycleOperationStatus.PENDING,
            LifecycleOperationStatus.RUNNING,
        ):
            return None

        move_to_error = _is_project_waiting_on(project_data, operation)
        result = StaleOperation(
            operation_id=str(operation.operation_id),
            project_slug=project_data.project.slug,
            type=operation.type,
            started_at=operation.started_at,
            project_moved_to_error=move_to_error,
        )
        if dry_run:
            return result

        operation.status = LifecycleOperationStatus.FAILED
        operation.error_message = (
            "Operation timed out: no completion callback received from the "
            "tools API."
        )
        operation.error_details = json.dumps(
            {
                "reason": "stale_operation",
                "stale_after_seconds": int(stale_after.total_seconds()),
                "detected_at": now.isoformat(),
            },
            sort_keys=True,
        )
        operation.finished_at = now
        operation.save(
            update_fields=[
                "status",
                "error_message",
                "error_details",
                "finished_at",
            ]
        )
        if move_to_error:
            project_data.transition_to(LifecycleState.ERROR)

    logger.error(
        "Lifecycle operation timed out without callback: operation_id=%s "
        "project_slug=%s type=%s started_at=%s project_moved_to_error=%s",
        result.operation_id,
        result.project_slug,
        result.type,
        result.started_at,
        result.project_moved_to_error,
    )
    return result


def _is_project_waiting_on(
    project_data: ProjectData, operation: LifecycleOperation
) -> bool:
    """True when the project is in the in-flight state matching this operation.

    A stale PENDING operation on a project that is still HOT (the request to the
    tools API never went out) must not change the project state.
    """
    return project_data.lifecycle_state == _IN_FLIGHT_STATE_BY_TYPE.get(
        operation.type
    ) and project_data.can_transition_to(LifecycleState.ERROR)
