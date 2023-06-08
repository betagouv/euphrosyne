from rest_framework.permissions import IsAdminUser

from ..permissions import is_lab_admin


class IsLabAdminUser(IsAdminUser):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and is_lab_admin(request.user)
