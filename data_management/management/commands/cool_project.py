import uuid
from django.utils import timezone
from django.core.management.base import BaseCommand

from data_management.models import (
    LifecycleOperation,
    LifecycleOperationStatus,
    LifecycleOperationType,
    LifecycleState,
    ProjectData,
)
from data_management.scheduler import _dispatch_cooling_operation


class Command(BaseCommand):
    help = "Cool project data."

    def add_arguments(self, parser):
        parser.add_argument("project_slug", type=str)

    def handle(self, *args, **options) -> None:
        project_slug = options["project_slug"]

        project_data = ProjectData.objects.get(
            project__slug=project_slug,
            lifecycle_state__in=[LifecycleState.HOT, LifecycleState.ERROR],
        )

        operation = LifecycleOperation.objects.create(
            operation_id=uuid.uuid4(),
            project_data=project_data,
            type=LifecycleOperationType.COOL,
            status=LifecycleOperationStatus.PENDING,
            started_at=timezone.now(),
        )

        if _dispatch_cooling_operation(project_data, operation):
            operation.status = LifecycleOperationStatus.RUNNING
            operation.save(update_fields=["status"])
            self.stdout.write(
                self.style.SUCCESS(
                    "Cooling scheduler accepted project=%s slug=%s operation=%s."
                    % (
                        project_data.project_id,
                        project_data.project.slug,
                        operation.operation_id,
                    )
                )
            )
        else:
            operation.status = LifecycleOperationStatus.FAILED
            operation.finished_at = timezone.now()
            operation.error_message = "Cooling scheduler failed to dispatch operation."
            operation.save(update_fields=["status", "finished_at", "error_message"])
            self.stdout.write(
                self.style.ERROR(
                    "Cooling scheduler failed to dispatch project=%s slug=%s operation=%s."
                    % (
                        project_data.project_id,
                        project_data.project.slug,
                        operation.operation_id,
                    )
                )
            )
