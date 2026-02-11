from __future__ import annotations

import logging
import uuid
from datetime import datetime
from http import HTTPStatus

import requests
from django.conf import settings
from django.db import connection, transaction
from django.db.models import Exists, OuterRef, QuerySet
from django.utils import timezone

from euphro_tools.project_data import post_cool_project

from .models import (
    LifecycleOperation,
    LifecycleOperationStatus,
    LifecycleOperationType,
    LifecycleState,
    ProjectData,
)

logger = logging.getLogger(__name__)

COOLING_BATCH_LIMIT = 3
TOOLS_API_TIMEOUT_SECONDS = 10


def _is_project_cooling_enabled() -> bool:
    return bool(settings.DATA_COOLING_ENABLE)


def _apply_locking(queryset: QuerySet[ProjectData]) -> QuerySet[ProjectData]:
    if connection.features.has_select_for_update:
        return queryset.select_for_update(
            skip_locked=connection.features.has_select_for_update_skip_locked
        )
    return queryset


def _mark_operation_failed(
    operation: LifecycleOperation,
    *,
    error_message: str,
    error_details: str | None,
    finished_at: datetime,
) -> None:
    operation.status = LifecycleOperationStatus.FAILED
    operation.error_message = error_message
    operation.error_details = error_details
    operation.finished_at = finished_at
    operation.save(
        update_fields=[
            "status",
            "error_message",
            "error_details",
            "finished_at",
        ]
    )


def _dispatch_cooling_operation(
    project_data: ProjectData,
    operation: LifecycleOperation,
) -> bool:
    operation_id = operation.operation_id
    try:
        response = post_cool_project(
            project_slug=project_data.project.slug,
            operation_id=str(operation_id),
            timeout=TOOLS_API_TIMEOUT_SECONDS,
        )
    except requests.RequestException as error:
        _mark_operation_failed(
            operation,
            error_message="Tools API request failed.",
            error_details=str(error),
            finished_at=timezone.now(),
        )
        logger.error(
            "Cooling scheduler project=%s slug=%s operation=%s accepted=%s status=%s error=%s",  # pylint: disable=line-too-long
            project_data.project_id,
            project_data.project.slug,
            operation_id,
            False,
            None,
            str(error),
        )
        return False

    if response.status_code == HTTPStatus.ACCEPTED:
        try:
            with transaction.atomic():
                operation.status = LifecycleOperationStatus.RUNNING
                operation.save(update_fields=["status"])
                project_data.transition_to(LifecycleState.COOLING, operation=operation)
        except ValueError as error:
            _mark_operation_failed(
                operation,
                error_message="Project lifecycle transition failed.",
                error_details=str(error),
                finished_at=timezone.now(),
            )
            logger.warning(
                "Cooling scheduler project=%s slug=%s operation=%s accepted=%s status=%s error=%s",  # pylint: disable=line-too-long
                project_data.project_id,
                project_data.project.slug,
                operation_id,
                False,
                response.status_code,
                str(error),
            )
            return False
        logger.info(
            "Cooling scheduler project=%s slug=%s operation=%s accepted=%s status=%s",
            project_data.project_id,
            project_data.project.slug,
            operation_id,
            True,
            response.status_code,
        )
        return True

    error_details = response.text
    _mark_operation_failed(
        operation,
        error_message=f"Tools API rejected request ({response.status_code}).",
        error_details=error_details,
        finished_at=timezone.now(),
    )
    logger.warning(
        "Cooling scheduler project=%s slug=%s operation=%s accepted=%s status=%s error=%s",  # pylint: disable=line-too-long
        project_data.project_id,
        project_data.project.slug,
        operation_id,
        False,
        response.status_code,
        error_details,
    )
    return False


def run_cooling_scheduler(
    *,
    limit: int = COOLING_BATCH_LIMIT,
) -> int:
    logger.info("Cooling scheduler run started.")
    enabled = _is_project_cooling_enabled()
    logger.info("Cooling scheduler enabled: %s", enabled)
    if not enabled:
        logger.info("Cooling scheduler disabled.")
        logger.info("Cooling scheduler run ended.")
        return 0

    now = timezone.now()

    active_cool_ops = LifecycleOperation.objects.filter(
        project_data_id=OuterRef("pk"),
        type=LifecycleOperationType.COOL,
        status__in=[
            LifecycleOperationStatus.PENDING,
            LifecycleOperationStatus.RUNNING,
        ],
    )
    eligible_qs = (
        ProjectData.objects.filter(
            lifecycle_state=LifecycleState.HOT,
            cooling_eligible_at__lte=now,
        )
        .annotate(has_active_cool=Exists(active_cool_ops))
        .filter(has_active_cool=False)
    )
    eligible_count = eligible_qs.count()
    logger.info("Cooling scheduler eligible projects: %s", eligible_count)

    enqueued_count = 0
    claimed: list[tuple[ProjectData, LifecycleOperation]] = []
    with transaction.atomic():
        locked_qs = _apply_locking(eligible_qs)
        selected = list(
            locked_qs.select_related("project").order_by("cooling_eligible_at", "pk")[
                :limit
            ]
        )
        logger.info("Cooling scheduler processing: %s", len(selected))

        for project_data in selected:
            # Claim work in DB first (short transaction), then do network calls
            # after commit to avoid holding row locks during HTTP.
            operation = LifecycleOperation.objects.create(
                operation_id=uuid.uuid4(),
                project_data=project_data,
                type=LifecycleOperationType.COOL,
                status=LifecycleOperationStatus.PENDING,
                bytes_total=project_data.project_size_bytes,
                files_total=project_data.file_count,
                started_at=now,
            )
            claimed.append((project_data, operation))

    for project_data, operation in claimed:
        if _dispatch_cooling_operation(project_data, operation):
            enqueued_count += 1

    logger.info("Cooling scheduler enqueued projects: %s", enqueued_count)
    logger.info("Cooling scheduler run ended.")
    return enqueued_count
