from __future__ import annotations

import uuid
from http import HTTPStatus
from typing import Callable

import requests
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext as _

from euphro_tools.project_data import post_cool_project, post_restore_project
from lab.models import Project

from .models import (
    LifecycleOperation,
    LifecycleOperationStatus,
    LifecycleOperationType,
    LifecycleState,
    ProjectData,
)

TOOLS_API_TIMEOUT_SECONDS = 10


class ProjectDataNotFoundError(Exception):
    pass


class LifecycleOperationNotAllowedError(Exception):
    def __init__(self, detail: str, *, lifecycle_state: str) -> None:
        super().__init__(detail)
        self.detail = detail
        self.lifecycle_state = lifecycle_state


class LifecycleOperationStartError(Exception):
    def __init__(self, detail: str, *, operation: LifecycleOperation) -> None:
        super().__init__(detail)
        self.detail = detail
        self.operation = operation


def trigger_cool_operation(
    project_id: int,
    *,
    post_function: Callable[..., requests.Response] | None = None,
) -> LifecycleOperation:
    return _trigger_operation(
        project_id,
        LifecycleOperationType.COOL,
        post_function=post_function,
    )


def trigger_restore_operation(
    project_id: int,
    *,
    post_function: Callable[..., requests.Response] | None = None,
) -> LifecycleOperation:
    return _trigger_operation(
        project_id,
        LifecycleOperationType.RESTORE,
        post_function=post_function,
    )


def is_retryable_operation(project_data: ProjectData) -> bool:
    last_operation = project_data.last_lifecycle_operation
    return bool(
        project_data.lifecycle_state == LifecycleState.ERROR
        and last_operation is not None
        and last_operation.status == LifecycleOperationStatus.FAILED
    )


def _trigger_operation(
    project_id: int,
    operation_type: str,
    *,
    post_function: Callable[..., requests.Response] | None = None,
) -> LifecycleOperation:
    with transaction.atomic():
        project_data = _get_locked_project_data(project_id)
        if project_data is None:
            raise ProjectDataNotFoundError

        if not _is_allowed_source(project_data, operation_type):
            raise LifecycleOperationNotAllowedError(
                _not_allowed_detail(operation_type),
                lifecycle_state=project_data.lifecycle_state,
            )

        operation = LifecycleOperation.objects.create(
            operation_id=uuid.uuid4(),
            project_data=project_data,
            type=operation_type,
            status=LifecycleOperationStatus.PENDING,
            started_at=timezone.now(),
        )

    try:
        response = _post_operation_request(
            operation_type=operation_type,
            project_slug=project_data.project.slug,
            operation_id=str(operation.operation_id),
            post_function=post_function,
        )
    except requests.RequestException as error:
        _mark_operation_start_failed(
            operation_id=operation.operation_id,
            error_message="Tools API request failed.",
            error_details=str(error),
        )
        raise LifecycleOperationStartError(
            _request_failed_detail(operation_type),
            operation=operation,
        ) from error

    if response.status_code != HTTPStatus.ACCEPTED:
        _mark_operation_start_failed(
            operation_id=operation.operation_id,
            error_message=(
                f"Tools API rejected {operation_type.lower()} request "
                f"({response.status_code})."
            ),
            error_details=response.text,
        )
        raise LifecycleOperationStartError(
            _request_rejected_detail(operation_type),
            operation=operation,
        )

    with transaction.atomic():
        locked_project_data = ProjectData.objects.select_for_update().get(
            pk=project_data.pk
        )
        locked_operation = LifecycleOperation.objects.select_for_update().get(
            operation_id=operation.operation_id
        )
        _transition_project_to_running_state(
            project_data=locked_project_data,
            operation_type=locked_operation.type,
        )
        locked_operation.status = LifecycleOperationStatus.RUNNING
        locked_operation.save(update_fields=["status"])

    operation.status = LifecycleOperationStatus.RUNNING
    return operation


def _get_locked_project_data(project_id: int) -> ProjectData | None:
    project = Project.objects.select_for_update().filter(pk=project_id).first()
    if project is None:
        return None

    project_data = ProjectData.for_project(project)
    return (
        ProjectData.objects.select_for_update()
        .select_related("project")
        .get(pk=project_data.pk)
    )


def _is_allowed_source(project_data: ProjectData, operation_type: str) -> bool:
    if operation_type == LifecycleOperationType.COOL:
        return _is_allowed_cool_source(project_data)
    return _is_allowed_restore_source(project_data)


def _is_allowed_cool_source(project_data: ProjectData) -> bool:
    if project_data.lifecycle_state == LifecycleState.HOT:
        return project_data.can_transition_to(LifecycleState.COOLING)
    if project_data.lifecycle_state == LifecycleState.ERROR:
        return _is_error_retry_for_operation(project_data, LifecycleOperationType.COOL)
    return False


def _is_allowed_restore_source(project_data: ProjectData) -> bool:
    return (
        project_data.lifecycle_state == LifecycleState.COOL
        or _is_error_retry_for_operation(project_data, LifecycleOperationType.RESTORE)
    )


def _is_error_retry_for_operation(
    project_data: ProjectData,
    operation_type: str,
) -> bool:
    if project_data.lifecycle_state != LifecycleState.ERROR:
        return False
    last_operation = project_data.last_lifecycle_operation
    if last_operation is None:
        return False
    return last_operation.type == operation_type


def _transition_project_to_running_state(
    *,
    project_data: ProjectData,
    operation_type: str,
) -> None:
    target_state = _running_target_state(operation_type)
    if project_data.lifecycle_state == LifecycleState.ERROR:
        project_data.lifecycle_state = target_state
        project_data.save(update_fields=["lifecycle_state"])
        return
    project_data.transition_to(target_state)


def _running_target_state(operation_type: str) -> LifecycleState:
    if operation_type == LifecycleOperationType.COOL:
        return LifecycleState.COOLING
    return LifecycleState.RESTORING


def _post_operation_request(
    *,
    operation_type: str,
    project_slug: str,
    operation_id: str,
    post_function: Callable[..., requests.Response] | None = None,
) -> requests.Response:
    if post_function is None:
        if operation_type == LifecycleOperationType.COOL:
            post_function = post_cool_project
        else:
            post_function = post_restore_project
    return post_function(
        project_slug=project_slug,
        operation_id=operation_id,
        timeout=TOOLS_API_TIMEOUT_SECONDS,
    )


def _mark_operation_start_failed(
    *,
    operation_id: uuid.UUID,
    error_message: str,
    error_details: str | None,
) -> None:
    with transaction.atomic():
        operation = LifecycleOperation.objects.select_for_update().get(
            operation_id=operation_id
        )
        operation.status = LifecycleOperationStatus.FAILED
        operation.error_message = error_message
        operation.error_details = error_details
        operation.finished_at = timezone.now()
        operation.save(
            update_fields=[
                "status",
                "error_message",
                "error_details",
                "finished_at",
            ]
        )


def _not_allowed_detail(operation_type: str) -> str:
    if operation_type == LifecycleOperationType.COOL:
        return _("Project lifecycle state does not allow cool.")
    return _("Project lifecycle state does not allow restore.")


def _request_failed_detail(operation_type: str) -> str:
    if operation_type == LifecycleOperationType.COOL:
        return _("Cool retry request failed while calling tools API.")
    return _("Restore request failed while calling tools API.")


def _request_rejected_detail(operation_type: str) -> str:
    if operation_type == LifecycleOperationType.COOL:
        return _("Cool retry request was rejected by tools API.")
    return _("Restore request was rejected by tools API.")
