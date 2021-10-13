from euphro_auth.models import User, UserGroups


def is_lab_admin(user: User):
    # [XXX] Peut-être pas nécessaire de mettre le is_superuser ici.
    return user.is_superuser or user.groups.filter(name=UserGroups.ADMIN.value).exists()
