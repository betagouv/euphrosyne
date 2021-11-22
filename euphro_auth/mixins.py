from typing import Optional, TypeVar

from django.db import models
from django.http import HttpRequest

# pylint: disable=invalid-name ; should be fixed with https://github.com/PyCQA/pylint/pull/5221
T = TypeVar("T", bound=models.Model)


class StaffUserAllowedMixin:
    @staticmethod
    def has_module_permission(request: HttpRequest) -> bool:
        return request.user.is_staff

    @staticmethod
    # pylint: disable=unused-argument
    def has_view_permission(request, obj: Optional[T] = None):
        return request.user.is_staff
