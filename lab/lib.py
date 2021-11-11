from euphro_auth.models import User, UserGroups
from lab.models import Project


def is_lab_admin(user: User) -> bool:
    return user.is_superuser or user.groups.filter(name=UserGroups.ADMIN.value).exists()


def is_project_leader(user: User, project: Project) -> bool:
    return project.participation_set.filter(user=user, is_leader=True).exists()
