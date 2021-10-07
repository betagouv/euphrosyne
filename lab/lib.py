from euphro_auth.models import User, UserGroups


def is_project_admin(user: User):
    # [XXX] Peut-être pas nécessaire de mettre le is_superuser ici. Tester de
    # virer le `if is_project_admin(...)` dans les has_x_permission
    return user.is_superuser or user.groups.filter(name=UserGroups.ADMIN.value).exists()
