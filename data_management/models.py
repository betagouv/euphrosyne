"""Run data lifecycle models and guards for COOL/RESTORE state changes.

Includes eligibility checks, verification against expected totals, and
state transitions that are validated before persisting.
"""

import uuid

from django.db import models
from django.db.models import F
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


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
    project_run_data = models.ForeignKey(
        "data_management.RunData",
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


class RunData(models.Model):
    """Store run-level lifecycle state and expected data totals."""

    run = models.OneToOneField(
        "lab.Run",
        on_delete=models.CASCADE,
        related_name="project_run_data",
    )
    lifecycle_state = models.CharField(
        max_length=32,
        choices=LifecycleState.choices,
        default=LifecycleState.HOT,
    )
    cooling_eligible_at = models.DateTimeField(null=True, blank=True)
    run_size_bytes = models.PositiveBigIntegerField(null=True, blank=True)
    file_count = models.PositiveBigIntegerField(null=True, blank=True)

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
                and verify_operation_success(
                    self, operation, LifecycleOperationType.COOL
                )
            )
        if target_state == LifecycleState.RESTORING:
            return self.lifecycle_state == LifecycleState.COOL
        if target_state == LifecycleState.HOT:
            return (
                self.lifecycle_state == LifecycleState.RESTORING
                and verify_operation_success(
                    self, operation, LifecycleOperationType.RESTORE
                )
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
    ) -> "RunData":
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
    run_data: "RunData",
    operation: "LifecycleOperation | None",
) -> bool:
    """Return True when copied totals match expected run data totals.

    This check guards COOL/HOT transitions from accepting partial moves.
    """
    if operation is None:
        return False
    if run_data.pk is None or operation.project_run_data_id != run_data.pk:
        return False
    if run_data.run_size_bytes is None or run_data.file_count is None:
        return False
    if operation.bytes_copied is None or operation.files_copied is None:
        return False
    return (
        operation.bytes_copied == run_data.run_size_bytes
        and operation.files_copied == run_data.file_count
    )


def verify_operation_success(
    run_data: "RunData",
    operation: "LifecycleOperation | None",
    operation_type: LifecycleOperationType,
) -> bool:
    """Return True when the operation succeeded and verification matches."""
    if operation is None:
        return False
    if operation.type != operation_type:
        return False
    if operation.status != LifecycleOperationStatus.SUCCEEDED:
        return False
    return verify_operation(run_data, operation)
