import uuid

from django.db import models
from django.db.models import F
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
    def last_lifecycle_operation(self):
        return self.lifecycle_operations.order_by(
            F("finished_at").desc(nulls_last=True),
            F("started_at").desc(nulls_last=True),
        ).first()

    class Meta:
        indexes = [
            models.Index(fields=["lifecycle_state"]),
            models.Index(fields=["cooling_eligible_at"]),
        ]
