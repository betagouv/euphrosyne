from typing import Generic, Optional, TypeVar

from django.core.exceptions import PermissionDenied
from django.db import models
from rest_framework.permissions import SAFE_METHODS, IsAdminUser

from lab.projects.models import Project

from ..permissions import is_lab_admin, is_project_leader

T = TypeVar("T", bound=models.Model)


class IsLabAdminUser(IsAdminUser):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and is_lab_admin(request.user)


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
