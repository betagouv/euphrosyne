from typing import Generic, Optional, TypeVar

from django.core.exceptions import PermissionDenied
from django.db import models
from rest_framework.permissions import SAFE_METHODS, BasePermission, IsAdminUser

from lab.projects.models import Project

from ..permissions import is_lab_admin, is_project_leader

T = TypeVar("T", bound=models.Model)


class IsLabAdminUser(IsAdminUser):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and is_lab_admin(request.user)


class IsLabAdminOrEuphrosyneBackend(IsLabAdminUser):
    """Check user is lab admin or is euphrosyne backend."""

    def has_permission(self, request, view):
        return super().has_permission(request, view) or (
            request.user.is_authenticated and request.user.email == "euphrosyne"
        )


class IsProjectMemberOrLabAdminOrEuphrosyneBackend(BasePermission):
    """Allow project members, lab admins, or the backend service account."""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.email == "euphrosyne" or is_lab_admin(request.user):
            return True

        project_slug = view.kwargs.get("project_slug")
        if not project_slug:
            return False

        matching_projects = Project.objects.filter(slug=project_slug)
        if not matching_projects.exists():
            return True

        return matching_projects.filter(members__id=request.user.id).exists()


class ProjectMembershipRequiredMixin(Generic[T], IsAdminUser):
    def get_related_project(self, obj: T | None = None) -> Optional[Project]:
        raise NotImplementedError()

    def has_object_permission(self, request, view, obj):
        project = self.get_related_project(obj)
        return super().has_object_permission(request, view, obj) and (
            is_lab_admin(request.user)
            or project.participation_set.filter(user=request.user).exists()
        )

    def check_object_permissions(self, request, obj):
        if not self.has_object_permission(request, self, obj):
            raise PermissionDenied()


class IsLeaderOrReadOnlyMixin(ProjectMembershipRequiredMixin):
    def get_related_project(self, obj: T | None = None) -> Optional[Project]:
        raise NotImplementedError()

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return super().has_object_permission(request, view, obj)
        return is_lab_admin(request.user) or is_project_leader(
            request.user, self.get_related_project(obj)
        )
