import enum
from functools import wraps
from typing import Optional

from django.http import HttpResponse, JsonResponse
from django.http.request import HttpRequest

from euphro_auth.models import User
from lab.models import Project
from shared.view_mixins import StaffUserRequiredMixin


class LabRole(enum.IntEnum):
    ANY_STAFF_USER = 0
    PROJECT_MEMBER = 1
    PROJECT_LEADER = 2
    LAB_ADMIN = 3


def get_user_permission_group(
    request: HttpRequest, project: Project
) -> Optional[LabRole]:
    if is_lab_admin(request.user):
        return LabRole.LAB_ADMIN
    member_participations = list(
        project.participation_set.filter(
            user__is_staff=True, user=request.user
        ).values_list("is_leader", flat=True)
    )
    if member_participations:
        is_leader = member_participations[0]
        if is_leader:
            return LabRole.PROJECT_LEADER
        return LabRole.PROJECT_MEMBER
    return LabRole.ANY_STAFF_USER


def is_lab_admin(user: User) -> bool:
    return user.is_superuser or getattr(user, "is_lab_admin", None)


def is_project_leader(user: User, project: Project) -> bool:
    return project.participation_set.filter(user=user, is_leader=True).exists()


class ProjectMembershipRequiredMixin(StaffUserRequiredMixin):
    # pylint: disable=arguments-differ
    def dispatch(
        self, request: HttpRequest, project_id: int, *args, **kwargs
    ) -> HttpResponse:
        response = super().dispatch(request, *args, **kwargs)
        if (
            not is_lab_admin(request.user)
            and not Project.objects.filter(
                id=project_id, members__id=request.user.id
            ).exists()
        ):
            return self.handle_no_permission()
        return response


def project_membership_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, project_id: int, *args, **kwargs):
        try:
            project = Project.objects.get(pk=project_id)
        except Project.DoesNotExist:
            return JsonResponse(data={}, status=404)
        if (
            not is_lab_admin(request.user)
            and not project.members.filter(id=request.user.id).exists()
        ):
            return JsonResponse(data={}, status=403)
        return view_func(request, project_id, *args, **kwargs)

    return _wrapped_view


def is_lab_admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, project_id: int, *args, **kwargs):
        if not is_lab_admin(request.user):
            return JsonResponse(data={}, status=403)
        return view_func(request, project_id, *args, **kwargs)

    return _wrapped_view
