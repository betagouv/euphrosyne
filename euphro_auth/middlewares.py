from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse

from .models import User


def _check_cgu_acceptance(user: User) -> bool:
    if not settings.FORCE_LAST_CGU_ACCEPTANCE_DT:
        return True
    if (
        user.cgu_accepted_at
        and user.cgu_accepted_at >= settings.FORCE_LAST_CGU_ACCEPTANCE_DT
    ):
        return True
    return False


class CGUAcceptanceMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and not _check_cgu_acceptance(request.user):
            if request.path not in [
                reverse("cgu_acceptance"),
                reverse("admin:logout"),
                reverse("static_cgu"),
            ]:
                return redirect("cgu_acceptance")
        response = self.get_response(request)
        return response
