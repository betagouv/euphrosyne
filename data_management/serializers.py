from __future__ import annotations

import json
from typing import Any

from rest_framework import serializers

from .models import LifecycleOperation


def _deserialize_error_details(error_details: str | None) -> Any | None:
    if not error_details:
        return None
    try:
        return json.loads(error_details)
    except json.JSONDecodeError:
        return error_details


def _compute_progress(
    *,
    bytes_total: int | None,
    bytes_copied: int | None,
    files_total: int | None,
    files_copied: int | None,
) -> float | None:
    if bytes_total is not None and bytes_total > 0:
        if bytes_copied is None:
            return None
        return bytes_copied / bytes_total
    if files_total is not None and files_total > 0:
        if files_copied is None:
            return None
        return files_copied / files_total
    return None


class LifecycleOperationErrorSerializer(serializers.Serializer):
    title = serializers.CharField(required=False)
    message = serializers.CharField(required=False)
    details = serializers.JSONField(required=False)
    code = serializers.JSONField(required=False)

    @classmethod
    def from_operation(cls, operation: LifecycleOperation) -> dict[str, Any] | None:
        details = _deserialize_error_details(operation.error_details)
        if operation.error_message is None and details is None:
            return None

        error_payload: dict[str, Any] = {}

        if operation.error_message:
            error_payload["title"] = operation.error_message
            error_payload["message"] = operation.error_message
        elif isinstance(details, dict):
            details_message = details.get("message")
            if isinstance(details_message, str):
                error_payload["message"] = details_message

        if details is not None:
            error_payload["details"] = details
            if isinstance(details, dict):
                error_code = details.get("code")
                if error_code is not None:
                    error_payload["code"] = error_code

        if not error_payload:
            return None
        return cls(error_payload).data

    def create(self, validated_data):
        raise NotImplementedError("Readonly serializer")

    def update(self, instance, validated_data):
        raise NotImplementedError("Readonly serializer")


class LifecycleOperationDetailSerializer(serializers.ModelSerializer):
    project_id = serializers.IntegerField(source="project_data.project_id")
    progress = serializers.SerializerMethodField()
    error = serializers.SerializerMethodField()

    class Meta:
        model = LifecycleOperation
        fields = (
            "operation_id",
            "project_id",
            "type",
            "status",
            "started_at",
            "finished_at",
            "bytes_total",
            "files_total",
            "bytes_copied",
            "files_copied",
            "progress",
            "error",
        )

    def get_progress(self, obj: LifecycleOperation) -> float | None:
        return _compute_progress(
            bytes_total=obj.bytes_total,
            bytes_copied=obj.bytes_copied,
            files_total=obj.files_total,
            files_copied=obj.files_copied,
        )

    def get_error(self, obj: LifecycleOperation) -> dict[str, Any] | None:
        return LifecycleOperationErrorSerializer.from_operation(obj)
