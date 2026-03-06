from __future__ import annotations

import json
import logging
import uuid
from http import HTTPStatus
from typing import Any, cast

import requests
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from euphro_auth.jwt.authentication import EuphrosyneAdminJWTAuthentication
from euphro_tools.project_data import post_cool_project, post_restore_project
from lab.api_views.permissions import IsLabAdminUser
from lab.models import Project
from lab.permissions import is_lab_admin

from .models import (
    LifecycleOperation,
    LifecycleOperationStatus,
    LifecycleOperationType,
    LifecycleState,
    ProjectData,
    verify_operation,
)
from .serializers import LifecycleOperationDetailSerializer

logger = logging.getLogger(__name__)
TOOLS_API_TIMEOUT_SECONDS = 10

TERMINAL_OPERATION_STATUSES = (
    LifecycleOperationStatus.SUCCEEDED,
    LifecycleOperationStatus.FAILED,
)
CALLBACK_STATUS_CHOICES = (
    LifecycleOperationStatus.SUCCEEDED,
    LifecycleOperationStatus.FAILED,
)

ALLOWED_RESTORE_SOURCE_STATES = (LifecycleState.COOL,)


class ProjectCoolTriggerAPIView(APIView):
    permission_classes = [IsLabAdminUser]

    def post(self, request: Request, project_id: int) -> Response:
        with transaction.atomic():
            project_data = _get_locked_project_data(project_id)
            if project_data is None:
                return Response(status=status.HTTP_404_NOT_FOUND)

            if not _is_allowed_cool_source(project_data):
                return Response(
                    {
                        "detail": "Project lifecycle state does not allow cool.",
                        "lifecycle_state": project_data.lifecycle_state,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            operation = LifecycleOperation.objects.create(
                operation_id=uuid.uuid4(),
                project_data=project_data,
                type=LifecycleOperationType.COOL,
                status=LifecycleOperationStatus.PENDING,
                started_at=timezone.now(),
            )

        try:
            operation_id = str(operation.operation_id)
            response = post_cool_project(
                project_slug=project_data.project.slug,
                operation_id=operation_id,
                timeout=TOOLS_API_TIMEOUT_SECONDS,
            )
        except requests.RequestException as error:
            _mark_operation_start_failed(
                operation_id=operation.operation_id,
                error_message="Tools API request failed.",
                error_details=str(error),
            )
            return Response(
                {
                    "detail": "Cool retry request failed while calling tools API.",
                    "operation_id": str(operation.operation_id),
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )

        if response.status_code != HTTPStatus.ACCEPTED:
            _mark_operation_start_failed(
                operation_id=operation.operation_id,
                error_message=f"Tools API rejected cool request ({response.status_code}).",  # pylint: disable=line-too-long
                error_details=response.text,
            )
            return Response(
                {
                    "detail": "Cool retry request was rejected by tools API.",
                    "operation_id": str(operation.operation_id),
                },
                status=status.HTTP_502_BAD_GATEWAY,
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

        return Response(
            {
                "operation_id": str(operation.operation_id),
                "lifecycle_state": LifecycleState.COOLING,
            },
            status=status.HTTP_202_ACCEPTED,
        )


class ProjectRestoreTriggerAPIView(APIView):
    permission_classes = [IsLabAdminUser]

    def post(self, request: Request, project_id: int) -> Response:
        with transaction.atomic():
            project_data = _get_locked_project_data(project_id)
            if project_data is None:
                return Response(status=status.HTTP_404_NOT_FOUND)

            if not _is_allowed_restore_source(project_data):
                return Response(
                    {
                        "detail": "Project lifecycle state does not allow restore.",
                        "lifecycle_state": project_data.lifecycle_state,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            operation = LifecycleOperation.objects.create(
                operation_id=uuid.uuid4(),
                project_data=project_data,
                type=LifecycleOperationType.RESTORE,
                status=LifecycleOperationStatus.PENDING,
                started_at=timezone.now(),
            )

        try:
            operation_id = str(operation.operation_id)
            response = post_restore_project(
                project_slug=project_data.project.slug,
                operation_id=operation_id,
                timeout=TOOLS_API_TIMEOUT_SECONDS,
            )
        except requests.RequestException as error:
            _mark_operation_start_failed(
                operation_id=operation.operation_id,
                error_message="Tools API request failed.",
                error_details=str(error),
            )
            return Response(
                {
                    "detail": "Restore request failed while calling tools API.",
                    "operation_id": str(operation.operation_id),
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )

        if response.status_code != HTTPStatus.ACCEPTED:
            _mark_operation_start_failed(
                operation_id=operation.operation_id,
                error_message=(
                    f"Tools API rejected restore request ({response.status_code})."
                ),
                error_details=response.text,
            )
            return Response(
                {
                    "detail": "Restore request was rejected by tools API.",
                    "operation_id": str(operation.operation_id),
                },
                status=status.HTTP_502_BAD_GATEWAY,
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

        return Response(
            {
                "operation_id": str(operation.operation_id),
                "lifecycle_state": LifecycleState.RESTORING,
            },
            status=status.HTTP_202_ACCEPTED,
        )


class LifecycleOperationDetailAPIView(APIView):
    permission_classes = [IsLabAdminUser]

    def get(self, request: Request, operation_id: uuid.UUID) -> Response:
        operation = (
            LifecycleOperation.objects.select_related("project_data")
            .filter(operation_id=operation_id)
            .first()
        )
        if operation is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = LifecycleOperationDetailSerializer(operation)
        return Response(serializer.data, status=status.HTTP_200_OK)


class LifecycleOperationCallbackSerializer(serializers.Serializer):
    operation_id = serializers.UUIDField()
    status = serializers.ChoiceField(choices=CALLBACK_STATUS_CHOICES)
    bytes_copied = serializers.IntegerField(
        required=False, allow_null=True, min_value=0
    )
    files_copied = serializers.IntegerField(
        required=False, allow_null=True, min_value=0
    )
    bytes_total = serializers.IntegerField(required=False, allow_null=True, min_value=0)
    files_total = serializers.IntegerField(required=False, allow_null=True, min_value=0)
    error_message = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )
    error_details = serializers.JSONField(required=False, allow_null=True)

    def create(self, validated_data: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError("LifecycleOperationCallbackSerializer is read-only.")

    def update(self, instance: Any, validated_data: dict[str, Any]) -> Any:
        raise NotImplementedError("LifecycleOperationCallbackSerializer is read-only.")


class LifecycleOperationCallbackAPIView(APIView):
    authentication_classes = [EuphrosyneAdminJWTAuthentication]

    def post(self, request: Request) -> Response:
        callback_data = self._validated_callback_data(request)
        operation_id = callback_data["operation_id"]

        with transaction.atomic():
            operation = _get_locked_operation(operation_id)
            if operation is None:
                return Response(status=status.HTTP_404_NOT_FOUND)

            project_data = ProjectData.objects.select_for_update().get(
                pk=operation.project_data_id
            )

            if operation.status in TERMINAL_OPERATION_STATUSES:
                return Response(status=status.HTTP_200_OK)

            callback_status = cast(str, callback_data["status"])
            if callback_status == LifecycleOperationStatus.FAILED:
                _handle_failed_callback(operation, project_data, callback_data)
            else:
                _handle_success_callback(operation, project_data, callback_data)

        return Response(status=status.HTTP_200_OK)

    @staticmethod
    def _validated_callback_data(request: Request) -> dict[str, Any]:
        serializer = LifecycleOperationCallbackSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)
        data["finished_at"] = timezone.now()
        return data


class ProjectLifecycleAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, project_slug: str) -> Response:
        if not is_lab_admin(request.user):
            return Response(status=status.HTTP_403_FORBIDDEN)

        project = get_object_or_404(Project, slug=project_slug)
        project_data = ProjectData.for_project(project)
        last_operation = project_data.last_lifecycle_operation

        return Response(
            data={
                "lifecycle_state": project_data.lifecycle_state,
                "last_operation_id": (
                    str(last_operation.operation_id) if last_operation else None
                ),
                "last_operation_type": last_operation.type if last_operation else None,
            },
            status=status.HTTP_200_OK,
        )


def _serialize_error_details(error_payload: Any) -> str | None:
    if error_payload is None:
        return None
    if isinstance(error_payload, str):
        return error_payload
    return json.dumps(error_payload, sort_keys=True)


def _transition_project_to_error(project_data: ProjectData) -> None:
    if project_data.lifecycle_state == LifecycleState.ERROR:
        return
    if project_data.can_transition_to(LifecycleState.ERROR):
        project_data.transition_to(LifecycleState.ERROR)
    else:
        logger.warning(
            "Skipping invalid transition to ERROR for project_data=%s from state=%s",
            project_data.pk,
            project_data.lifecycle_state,
        )


def _verified_target_state(operation_type: str) -> LifecycleState:
    if operation_type == LifecycleOperationType.COOL:
        return LifecycleState.COOL
    return LifecycleState.HOT


def _get_locked_project_data(project_id: int) -> ProjectData | None:
    return (
        ProjectData.objects.select_for_update()
        .select_related("project")
        .filter(project_id=project_id)
        .first()
    )


def _running_target_state(operation_type: str) -> LifecycleState:
    if operation_type == LifecycleOperationType.COOL:
        return LifecycleState.COOLING
    return LifecycleState.RESTORING


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


def _is_allowed_cool_source(project_data: ProjectData) -> bool:
    if project_data.lifecycle_state == LifecycleState.HOT:
        return project_data.can_transition_to(LifecycleState.COOLING)
    if project_data.lifecycle_state == LifecycleState.ERROR:
        return _is_error_retry_for_operation(project_data, LifecycleOperationType.COOL)
    return False


def _is_allowed_restore_source(project_data: ProjectData) -> bool:
    return (
        project_data.lifecycle_state in ALLOWED_RESTORE_SOURCE_STATES
        or _is_error_retry_for_operation(project_data, LifecycleOperationType.RESTORE)
    )


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


def _mark_operation_start_failed(
    *,
    operation_id: Any,
    error_message: str,
    error_details: str | None,
) -> None:
    with transaction.atomic():
        operation = (
            LifecycleOperation.objects.select_for_update()
            .select_related("project_data")
            .get(operation_id=operation_id)
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


def _get_locked_operation(operation_id: Any) -> LifecycleOperation | None:
    try:
        return (
            LifecycleOperation.objects.select_for_update()
            .select_related("project_data")
            .get(operation_id=operation_id)
        )
    except LifecycleOperation.DoesNotExist:
        return None


def _handle_failed_callback(
    operation: LifecycleOperation,
    project_data: ProjectData,
    callback_data: dict[str, Any],
) -> None:
    error_message = cast(str | None, callback_data.get("error_message"))
    error_details_payload = callback_data.get("error_details")

    operation.status = LifecycleOperationStatus.FAILED
    operation.error_message = error_message or "Tools API reported operation failure."
    operation.error_details = _serialize_error_details(error_details_payload)
    operation.finished_at = callback_data["finished_at"]
    operation.save(
        update_fields=[
            "status",
            "error_message",
            "error_details",
            "finished_at",
        ]
    )
    _transition_project_to_error(project_data)


def _handle_success_callback(
    operation: LifecycleOperation,
    project_data: ProjectData,
    callback_data: dict[str, Any],
) -> None:
    bytes_copied = cast(int | None, callback_data.get("bytes_copied"))
    files_copied = cast(int | None, callback_data.get("files_copied"))
    bytes_total = cast(int | None, callback_data.get("bytes_total"))
    files_total = cast(int | None, callback_data.get("files_total"))

    operation.bytes_copied = bytes_copied
    operation.files_copied = files_copied
    if files_total is not None:
        operation.files_total = files_total
    if bytes_total is not None:
        operation.bytes_total = bytes_total

    if verify_operation(operation):
        _handle_verified_success(operation, project_data, callback_data)
        return

    _handle_verification_failure(
        operation,
        project_data,
        bytes_copied=bytes_copied,
        files_copied=files_copied,
        finished_at=callback_data["finished_at"],
    )


def _handle_verified_success(
    operation: LifecycleOperation,
    project_data: ProjectData,
    callback_data: dict[str, Any],
) -> None:
    operation.status = LifecycleOperationStatus.SUCCEEDED
    operation.error_message = None
    operation.error_details = None
    operation.finished_at = callback_data["finished_at"]

    try:
        project_data.transition_to(
            _verified_target_state(operation.type), operation=operation
        )
    except ValueError as error:
        operation.status = LifecycleOperationStatus.FAILED
        operation.error_message = "Project lifecycle transition failed."
        operation.error_details = str(error)
        _transition_project_to_error(project_data)

    operation.save(
        update_fields=[
            "status",
            "bytes_total",
            "files_total",
            "bytes_copied",
            "files_copied",
            "error_message",
            "error_details",
            "finished_at",
        ]
    )


def _handle_verification_failure(
    operation: LifecycleOperation,
    project_data: ProjectData,
    *,
    bytes_copied: int | None,
    files_copied: int | None,
    finished_at: Any,
) -> None:
    verification_error = {
        "reason": "verification_mismatch",
        "expected": {
            "bytes_total": operation.bytes_total,
            "files_total": operation.files_total,
        },
        "received": {
            "bytes_copied": bytes_copied,
            "files_copied": files_copied,
        },
    }
    operation.status = LifecycleOperationStatus.FAILED
    operation.error_message = "Verification failed."
    operation.error_details = json.dumps(verification_error, sort_keys=True)
    operation.finished_at = finished_at
    operation.save(
        update_fields=[
            "status",
            "bytes_total",
            "files_total",
            "bytes_copied",
            "files_copied",
            "error_message",
            "error_details",
            "finished_at",
        ]
    )
    _transition_project_to_error(project_data)
