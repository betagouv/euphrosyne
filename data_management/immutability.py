from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _

from data_management.models import LifecycleState, ProjectData

if TYPE_CHECKING:
    from lab.projects.models import Project


IMMUTABLE_LIFECYCLE_STATES = frozenset(
    {
        LifecycleState.COOL,
        LifecycleState.COOLING,
    }
)
PROJECT_IMMUTABLE_ERROR = "PROJECT_IMMUTABLE"
PROJECT_IMMUTABLE_MESSAGE = _(
    "Project is read-only while lifecycle_state is COOL or COOLING. "
    "Restore the project to HOT to modify files or create runs."
)


@dataclass(frozen=True)
class ProjectImmutablePayload:
    error: str
    message: str
    lifecycle_state: str


class ProjectImmutableError(PermissionDenied):
    def __init__(self, *, lifecycle_state: str):
        self.payload = ProjectImmutablePayload(
            error=PROJECT_IMMUTABLE_ERROR,
            message=str(PROJECT_IMMUTABLE_MESSAGE),
            lifecycle_state=lifecycle_state,
        )
        super().__init__(self.payload.message)


def is_lifecycle_state_immutable(lifecycle_state: str) -> bool:
    return lifecycle_state in IMMUTABLE_LIFECYCLE_STATES


def is_project_data_immutable(project: "Project") -> bool:
    project_data = ProjectData.for_project(project)
    return is_lifecycle_state_immutable(project_data.lifecycle_state)


def ensure_project_data_writable(project: "Project") -> None:
    project_data = ProjectData.for_project(project)
    if is_lifecycle_state_immutable(project_data.lifecycle_state):
        raise ProjectImmutableError(lifecycle_state=project_data.lifecycle_state)
