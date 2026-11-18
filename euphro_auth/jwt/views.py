import datetime
import logging
from typing import cast

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from ..models import User
from .tokens import TOKEN_SERVICES

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["GET", "POST"])
def service_token_view(request: HttpRequest, service: str) -> HttpResponse:
    """Issue a refresh token to paste into an application of TOKEN_SERVICES,
    which opens this page in a new window. AccountGatesMiddleware already
    requires a verified session from administrators while MFA is enforced."""
    token_service = TOKEN_SERVICES.get(service)
    if token_service is None:
        raise Http404
    user = cast(User, request.user)
    if not token_service.allowed(user):
        raise PermissionDenied
    # A window opened by the application: no platform header, menu or footer.
    context: dict = {"service": token_service, "is_popup": True}
    if request.method == "POST":
        refresh = token_service.issue(user)
        logger.info(
            "%s token issued for user %s (jti %s)",
            token_service.name,
            user.pk,
            refresh["jti"],
        )
        context["refresh_token"] = str(refresh)
        context["expires_at"] = timezone.localtime(
            datetime.datetime.fromtimestamp(refresh["exp"], tz=datetime.UTC)
        )
    return render(request, "euphro_auth/service_token.html", context)
