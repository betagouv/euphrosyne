import enum
from typing import Optional

from django.http.request import HttpRequest

from euphro_auth.models import User
from lab.models import Project


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
