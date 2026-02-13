from __future__ import annotations

import json
import logging
from typing import Any, cast

from django.db import transaction
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from euphro_auth.jwt.authentication import EuphrosyneAdminJWTAuthentication

from .models import (
    LifecycleOperation,
    LifecycleOperationStatus,
    LifecycleOperationType,
    LifecycleState,
    ProjectData,
    verify_operation,
)

logger = logging.getLogger(__name__)

TERMINAL_OPERATION_STATUSES = (
    LifecycleOperationStatus.SUCCEEDED,
    LifecycleOperationStatus.FAILED,
)
CALLBACK_STATUS_CHOICES = (
    LifecycleOperationStatus.SUCCEEDED,
    LifecycleOperationStatus.FAILED,
)


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
    permission_classes = [IsAuthenticated]

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
