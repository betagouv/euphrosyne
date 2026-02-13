"""Project data lifecycle models and guards for COOL/RESTORE state changes.

Includes eligibility checks, verification against expected totals, and
state transitions that are validated before persisting.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from django.db import models
from django.db.models import F
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from lab.projects.models import Project


class LifecycleState(models.TextChoices):
    HOT = "HOT", _("Hot")
    COOLING = "COOLING", _("Cooling")
    COOL = "COOL", _("Cool")
    RESTORING = "RESTORING", _("Restoring")
    ERROR = "ERROR", _("Error")


class LifecycleOperationType(models.TextChoices):
    COOL = "COOL", _("Cool")
    RESTORE = "RESTORE", _("Restore")


class LifecycleOperationStatus(models.TextChoices):
    PENDING = "PENDING", _("Pending")
    RUNNING = "RUNNING", _("Running")
    SUCCEEDED = "SUCCEEDED", _("Succeeded")
    FAILED = "FAILED", _("Failed")


class LifecycleOperation(models.Model):
    """Track cooling/restore operations and their verification metrics."""

    operation_id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )
    project_data = models.ForeignKey(
        "data_management.ProjectData",
        on_delete=models.CASCADE,
        related_name="lifecycle_operations",
    )
    type = models.CharField(max_length=16, choices=LifecycleOperationType.choices)
    status = models.CharField(
        max_length=16,
        choices=LifecycleOperationStatus.choices,
        default=LifecycleOperationStatus.PENDING,
    )
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    bytes_total = models.PositiveBigIntegerField(null=True, blank=True)
    files_total = models.PositiveBigIntegerField(null=True, blank=True)
    bytes_copied = models.PositiveBigIntegerField(null=True, blank=True)
    files_copied = models.PositiveBigIntegerField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    error_details = models.TextField(null=True, blank=True)


def _compute_initial_cooling_eligible_at(created_at: datetime) -> datetime:
    return created_at + timedelta(days=30 * 6)


class ProjectData(models.Model):
    """Store project-level lifecycle state and eligibility metadata."""

    project = models.OneToOneField(
        "lab.Project",
        on_delete=models.CASCADE,
        related_name="project_data",
    )
    lifecycle_state = models.CharField(
        max_length=32,
        choices=LifecycleState.choices,
        default=LifecycleState.HOT,
    )
    cooling_eligible_at = models.DateTimeField(null=True, blank=True)

    @classmethod
    def for_project(cls, project: Project) -> "ProjectData":
        created_at = project.created or timezone.now()
        cooling_default = _compute_initial_cooling_eligible_at(created_at)
        try:
            project_data = project.project_data
        except cls.DoesNotExist:
            project_data, _ = cls.objects.get_or_create(
                project=project, defaults={"cooling_eligible_at": cooling_default}
            )
        if project_data.cooling_eligible_at is None:
            project_data.cooling_eligible_at = cooling_default
            project_data.save(update_fields=["cooling_eligible_at"])
        return project_data

    @property
    def last_lifecycle_operation(self) -> LifecycleOperation | None:
        return self.lifecycle_operations.order_by(
            F("finished_at").desc(nulls_last=True),
            F("started_at").desc(nulls_last=True),
        ).first()

    def is_cooling_eligible(self) -> bool:
        """Return True when cooling_eligible_at is set and in the past."""
        if self.cooling_eligible_at is None:
            return False
        return self.cooling_eligible_at <= timezone.now()

    def can_transition_to(
        self,
        target_state: LifecycleState,
        *,
        operation: LifecycleOperation | None = None,
    ) -> bool:
        """Return True when a lifecycle transition is allowed.

        Operations are only required for COOL/HOT transitions, where a
        SUCCEEDED operation must be verified against expected totals.
        """
        if target_state == LifecycleState.COOLING:
            return (
                self.lifecycle_state == LifecycleState.HOT
                and self.is_cooling_eligible()
            )
        if target_state == LifecycleState.COOL:
            return (
                self.lifecycle_state == LifecycleState.COOLING
                and operation is not None
                and operation.project_data_id == self.pk
                and verify_operation_success(operation, LifecycleOperationType.COOL)
            )
        if target_state == LifecycleState.RESTORING:
            return self.lifecycle_state == LifecycleState.COOL
        if target_state == LifecycleState.HOT:
            return (
                self.lifecycle_state == LifecycleState.RESTORING
                and operation is not None
                and operation.project_data_id == self.pk
                and verify_operation_success(operation, LifecycleOperationType.RESTORE)
            )
        if target_state == LifecycleState.ERROR:
            return self.lifecycle_state in (
                LifecycleState.COOLING,
                LifecycleState.RESTORING,
            )
        return False

    def transition_to(
        self,
        target_state: LifecycleState,
        *,
        operation: LifecycleOperation | None = None,
    ) -> "ProjectData":
        """Persist a lifecycle transition after guard checks pass."""
        if not self.can_transition_to(target_state, operation=operation):
            raise ValueError(
                "Invalid lifecycle transition from "
                f"{self.lifecycle_state} to {target_state}."
            )
        self.lifecycle_state = target_state
        self.save(update_fields=["lifecycle_state"])
        return self

    class Meta:
        indexes = [
            models.Index(fields=["lifecycle_state"]),
            models.Index(fields=["cooling_eligible_at"]),
        ]


def verify_operation(
    operation: "LifecycleOperation",
) -> bool:
    """Return True when copied totals match expected operation totals.

    This check guards COOL/HOT transitions from accepting partial moves.
    """

    if (
        operation.bytes_copied is None
        or operation.files_copied is None
        or operation.bytes_total is None
        or operation.files_total is None
    ):
        return False
    return (
        operation.bytes_copied == operation.bytes_total
        and operation.files_copied == operation.files_total
    )


def verify_operation_success(
    operation: "LifecycleOperation",
    operation_type: LifecycleOperationType,
) -> bool:
    """Return True when the operation succeeded and verification matches."""
    if operation is None:
        return False
    if operation.type != operation_type:
        return False
    if operation.status != LifecycleOperationStatus.SUCCEEDED:
        return False
    return verify_operation(operation)
