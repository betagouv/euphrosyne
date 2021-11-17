import enum
from dataclasses import dataclass
from typing import Optional, TypeVar

from django.db import models
from django.http.request import HttpRequest

from lab.lib import is_lab_admin
from lab.models import Project

# pylint: disable=invalid-name ; should be fixed with https://github.com/PyCQA/pylint/pull/5221
T = TypeVar("T", bound=models.Model)


class LabRole(enum.IntEnum):
    NON_PARTICIPANT = 0
    PROJECT_MEMBER = 1
    PROJECT_LEADER = 2
    LAB_ADMIN = 3


@dataclass
class LabPermission:
    """Define minimum permissions for each class based view action
    (add, change, delete, view).
    Default permission for every action is lab admin."""

    add_permission: LabRole = LabRole.LAB_ADMIN
    change_permission: LabRole = LabRole.LAB_ADMIN
    delete_permission: LabRole = LabRole.LAB_ADMIN
    view_permission: LabRole = LabRole.LAB_ADMIN


class LabPermissionMixin:
    """Mixin used in class based view to set permissions.
    The view class using it must implement `get_related_project` and return
    the project related to the object passed in permission action view
    methods (`has_view_permission`, ...).
    The property `lab_permissions` is used to set permissions for the view."""

    project: Project
    lab_permissions: LabPermission = LabPermission()

    def get_related_project(self, obj: Optional[T] = None) -> Optional[Project]:
        raise NotImplementedError()

    def has_view_permission(
        self, request: HttpRequest, obj: Optional[T] = None
    ) -> bool:
        project = self.get_related_project(obj)
        return (
            not project
            or self._get_user_permission_group(request, project)
            >= self.lab_permissions.view_permission
        ) and super().has_view_permission(request, project)

    def has_add_permission(
        self, request: HttpRequest, obj: Optional[Project] = None
    ) -> bool:
        project = self.get_related_project(obj)
        return (
            not project
            or self._get_user_permission_group(request, project)
            >= self.lab_permissions.add_permission
        ) and super().has_add_permission(request)

    def has_change_permission(
        self, request: HttpRequest, obj: Optional[T] = None
    ) -> bool:
        project = self.get_related_project(obj)
        return (
            not project
            or self._get_user_permission_group(request, project)
            >= self.lab_permissions.change_permission
        ) and super().has_view_permission(request, project)

    def has_delete_permission(
        self, request: HttpRequest, obj: Optional[T] = None
    ) -> bool:
        project = self.get_related_project(obj)
        return (
            not project
            or self._get_user_permission_group(request, project)
            >= self.lab_permissions.delete_permission
        ) and super().has_view_permission(request, project)

    def _get_user_permission_group(
        self, request: HttpRequest, project: Project
    ) -> Optional[LabRole]:
        if is_lab_admin(request.user):
            return LabRole.LAB_ADMIN
        project_member_qs = project.participation_set.filter(user=request.user)
        if project_member_qs.exists():
            if project_member_qs.filter(is_leader=True).exists():
                return LabRole.PROJECT_LEADER
            return LabRole.PROJECT_MEMBER
        return LabRole.NON_PARTICIPANT
