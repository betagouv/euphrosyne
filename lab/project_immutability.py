from __future__ import annotations

from typing import TYPE_CHECKING

from django.apps import apps

if TYPE_CHECKING:
    from .projects.models import Project


def ensure_project_data_writable(project: "Project") -> None:
    if not apps.is_installed("data_management"):
        return
    # pylint: disable=import-outside-toplevel
    from data_management.immutability import (
        ensure_project_data_writable as ensure_dm_project_writable,
    )

    ensure_dm_project_writable(project)


def is_project_data_immutable(project: "Project") -> bool:
    if not apps.is_installed("data_management"):
        return False
    # pylint: disable=import-outside-toplevel
    from data_management.immutability import (
        is_project_data_immutable as is_dm_project_immutable,
    )

    return is_dm_project_immutable(project)
