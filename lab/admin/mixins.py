from dataclasses import dataclass
from typing import Optional, TypeVar

from django.db import models
from django.http.request import HttpRequest

from ..models import Project
from ..permissions import LabRole, get_user_permission_group, is_lab_admin

# pylint: disable=invalid-name ; should be fixed with https://github.com/PyCQA/pylint/pull/5221
T = TypeVar("T", bound=models.Model)


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
        return request.user.is_staff and (
            not project
            or get_user_permission_group(request, project)
            >= self.lab_permissions.view_permission
        )

    def has_add_permission(
        self, request: HttpRequest, obj: Optional[Project] = None
    ) -> bool:
        project = self.get_related_project(obj)
        if not project:
            if self.lab_permissions.add_permission == LabRole.ANY_STAFF_USER:
                return True
            return is_lab_admin(request.user)
        return (
            get_user_permission_group(request, project)
            >= self.lab_permissions.add_permission
        )

    def has_change_permission(
        self, request: HttpRequest, obj: Optional[T] = None
    ) -> bool:
        project = self.get_related_project(obj)
        return request.user.is_staff and (
            not project
            or get_user_permission_group(request, project)
            >= self.lab_permissions.change_permission
        )

    def has_delete_permission(
        self, request: HttpRequest, obj: Optional[T] = None
    ) -> bool:
        project = self.get_related_project(obj)
        return request.user.is_staff and (
            not project
            or get_user_permission_group(request, project)
            >= self.lab_permissions.delete_permission
        )

    # pylint: disable=no-self-use
    def has_module_permission(self, request: HttpRequest) -> bool:
        return request.user.is_staff


class LabAdminAllowedMixin:
    """Gives permission to every action to lab admin and restricts others."""

    # pylint: disable=unused-argument,no-self-use
    def has_module_permission(self, request: HttpRequest) -> bool:
        return request.user.is_staff and is_lab_admin(request.user)

    # pylint: disable=unused-argument,no-self-use
    def has_view_permission(self, request: HttpRequest, obj: Optional[T] = None):
        return request.user.is_staff and is_lab_admin(request.user)

    # pylint: disable=unused-argument,no-self-use
    def has_add_permission(self, request: HttpRequest, obj: Optional[T] = None):
        return request.user.is_staff and is_lab_admin(request.user)

    # pylint: disable=unused-argument,no-self-use
    def has_change_permission(self, request: HttpRequest, obj: Optional[T] = None):
        return request.user.is_staff and is_lab_admin(request.user)

    # pylint: disable=unused-argument,no-self-use
    def has_delete_permission(self, request: HttpRequest, obj: Optional[T] = None):
        return request.user.is_staff and is_lab_admin(request.user)
