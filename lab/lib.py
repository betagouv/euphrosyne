from euphro_auth.models import User, UserGroups


def is_lab_admin(user: User):
    return user.is_superuser or user.groups.filter(name=UserGroups.ADMIN.value).exists()
