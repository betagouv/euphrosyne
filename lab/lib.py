from euphro_auth.models import User
from lab.models import Project


def is_lab_admin(user: User) -> bool:
    return user.is_superuser or user.is_lab_admin


def is_project_leader(user: User, project: Project) -> bool:
    return project.participation_set.filter(user=user, is_leader=True).exists()
