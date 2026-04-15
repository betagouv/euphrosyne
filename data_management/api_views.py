from __future__ import annotations

import json
import logging
import uuid
from typing import Any, cast

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.settings import api_settings as rf_api_settings
from rest_framework.views import APIView

from euphro_auth.jwt.authentication import EuphrosyneAdminJWTAuthentication
from euphro_tools.project_data import post_cool_project, post_restore_project
from lab.api_views.permissions import (
    IsLabAdminUser,
    IsProjectMemberOrLabAdminOrEuphrosyneBackend,
)
from lab.models import Project

from .models import (
    FromDataDeletionStatus,
    LifecycleOperation,
    LifecycleOperationStatus,
    LifecycleOperationType,
    LifecycleState,
    ProjectData,
    verify_operation,
)
from .operations import (
    LifecycleOperationNotAllowedError,
    LifecycleOperationStartError,
    ProjectDataNotFoundError,
    trigger_cool_operation,
    trigger_restore_operation,
)
from .serializers import LifecycleOperationDetailSerializer

logger = logging.getLogger(__name__)

TERMINAL_OPERATION_STATUSES = (
    LifecycleOperationStatus.SUCCEEDED,
    LifecycleOperationStatus.FAILED,
)
CALLBACK_STATUS_CHOICES = (
    LifecycleOperationStatus.SUCCEEDED,
    LifecycleOperationStatus.FAILED,
)
FROM_DATA_DELETION_PHASE = "FROM_DATA_DELETION"
CALLBACK_PHASE_CHOICES = (FROM_DATA_DELETION_PHASE,)
FROM_DATA_DELETION_STATUS_CHOICES = (
    FromDataDeletionStatus.SUCCEEDED,
    FromDataDeletionStatus.FAILED,
)


class ProjectCoolTriggerAPIView(APIView):
    permission_classes = [IsLabAdminUser]

    def post(self, request: Request, project_id: int) -> Response:
        try:
            operation = trigger_cool_operation(
                project_id,
                post_function=post_cool_project,
            )
        except ProjectDataNotFoundError:
            return Response(status=status.HTTP_404_NOT_FOUND)
        except LifecycleOperationNotAllowedError as error:
            return Response(
                {
                    "detail": error.detail,
                    "lifecycle_state": error.lifecycle_state,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except LifecycleOperationStartError as error:
            return Response(
                {
                    "detail": error.detail,
                    "operation_id": str(error.operation.operation_id),
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )

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
        try:
            operation = trigger_restore_operation(
                project_id,
                post_function=post_restore_project,
            )
        except ProjectDataNotFoundError:
            return Response(status=status.HTTP_404_NOT_FOUND)
        except LifecycleOperationNotAllowedError as error:
            return Response(
                {
                    "detail": error.detail,
                    "lifecycle_state": error.lifecycle_state,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except LifecycleOperationStartError as error:
            return Response(
                {
                    "detail": error.detail,
                    "operation_id": str(error.operation.operation_id),
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )

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
    phase = serializers.ChoiceField(
        choices=CALLBACK_PHASE_CHOICES,
        required=False,
    )
    status = serializers.ChoiceField(choices=CALLBACK_STATUS_CHOICES, required=False)
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
    from_data_deletion_status = serializers.ChoiceField(
        choices=FROM_DATA_DELETION_STATUS_CHOICES,
        required=False,
    )
    error = serializers.JSONField(required=False, allow_null=True)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        phase = attrs.get("phase")
        if phase == FROM_DATA_DELETION_PHASE:
            if "from_data_deletion_status" not in attrs:
                raise serializers.ValidationError(
                    {
                        "from_data_deletion_status": _(
                            "This field is required for deletion callbacks."
                        )
                    }
                )
            return attrs

        if "status" not in attrs:
            raise serializers.ValidationError({"status": _("This field is required.")})
        return attrs

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

            if callback_data.get("phase") == FROM_DATA_DELETION_PHASE:
                _handle_from_data_deletion_callback(operation, callback_data)
                return Response(status=status.HTTP_200_OK)

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
        received_at = timezone.now()
        data["received_at"] = received_at
        if data.get("phase") != FROM_DATA_DELETION_PHASE:
            data["finished_at"] = received_at
        return data


class ProjectLifecycleAPIView(APIView):
    permission_classes = [IsProjectMemberOrLabAdminOrEuphrosyneBackend]
    authentication_classes = [
        EuphrosyneAdminJWTAuthentication,
        *rf_api_settings.DEFAULT_AUTHENTICATION_CLASSES,
    ]

    def get(self, request: Request, project_slug: str) -> Response:

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


def _get_locked_operation(operation_id: Any) -> LifecycleOperation | None:
    try:
        return (
            LifecycleOperation.objects.select_for_update()
            .select_related("project_data")
            .get(operation_id=operation_id)
        )
    except LifecycleOperation.DoesNotExist:
        return None


def _handle_from_data_deletion_callback(
    operation: LifecycleOperation,
    callback_data: dict[str, Any],
) -> None:
    if operation.from_data_deletion_status == FromDataDeletionStatus.NOT_REQUESTED:
        return

    if operation.from_data_deletion_status in (
        FromDataDeletionStatus.SUCCEEDED,
        FromDataDeletionStatus.FAILED,
    ):
        return

    deletion_status = cast(str, callback_data["from_data_deletion_status"])
    if deletion_status == FromDataDeletionStatus.SUCCEEDED:
        operation.from_data_deletion_status = FromDataDeletionStatus.SUCCEEDED
        operation.from_data_deleted_at = callback_data["received_at"]
        operation.from_data_deletion_error = None
    else:
        error_payload = callback_data.get("error")
        operation.from_data_deletion_status = FromDataDeletionStatus.FAILED
        operation.from_data_deleted_at = None
        operation.from_data_deletion_error = (
            _serialize_error_details(error_payload)
            or "Tools API reported source data deletion failure."
        )

    operation.save(
        update_fields=[
            "from_data_deletion_status",
            "from_data_deleted_at",
            "from_data_deletion_error",
        ]
    )


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
