import logging
from typing import cast

from django.contrib import admin, messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from django.views.decorators.cache import never_cache

from lab.permissions import is_lab_admin

from ..emails import send_mfa_enrolled_email
from ..models import User
from . import services
from .forms import MFACodeForm

logger = logging.getLogger(__name__)

INVALID_CODE_MESSAGE = gettext_lazy("Invalid code. Please try again.")


def _ensure_lab_admin(request: HttpRequest) -> None:
    if not is_lab_admin(request.user):
        raise PermissionDenied


def _page_context(title: str, **kwargs) -> dict:
    return {"title": title, "site_title": "Euphrosyne", **kwargs}


@never_cache
@login_required
def mfa_verify_view(request: HttpRequest) -> HttpResponse:
    _ensure_lab_admin(request)
    user = cast(User, request.user)
    next_url = services.get_safe_next_url(request)
    if services.is_verified(user):
        return redirect(next_url)
    if not services.has_confirmed_totp_device(user):
        return redirect(services.get_mfa_url(user, next_url))

    form = MFACodeForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        device = services.verify_code(user, form.cleaned_data["code"])
        if device is not None:
            services.mark_session_verified(request, device)
            return redirect(next_url)
        form.add_error(None, INVALID_CODE_MESSAGE)

    return render(
        request,
        "euphro_auth/mfa/verify.html",
        _page_context(_("Two-factor authentication"), form=form, next=next_url),
    )


@never_cache
@login_required
def mfa_setup_view(request: HttpRequest) -> HttpResponse:
    _ensure_lab_admin(request)
    user = cast(User, request.user)
    next_url = services.get_safe_next_url(request)
    if services.has_confirmed_totp_device(user):
        # Adding a device requires removing the current one from a verified
        # session, on the account security page.
        if services.is_verified(user):
            return redirect(reverse("admin:account_security"))
        return redirect(services.get_mfa_url(user, next_url))

    device = services.get_or_create_pending_totp_device(user)
    form = MFACodeForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        if services.confirm_totp_enrollment(user, device, form.cleaned_data["code"]):
            services.mark_session_verified(request, device)
            send_mfa_enrolled_email(user)
            messages.success(
                request,
                _("Two-factor authentication is now enabled on your account."),
            )
            return redirect(next_url)
        form.add_error(None, INVALID_CODE_MESSAGE)

    return render(
        request,
        "euphro_auth/mfa/setup.html",
        _page_context(
            _("Set up two-factor authentication"),
            form=form,
            next=next_url,
            qr_code_svg=services.get_totp_qr_code_svg(device),
            secret=services.get_totp_secret(device),
        ),
    )


def account_security_view(request: HttpRequest) -> HttpResponse:
    """Manage the second factor. Wrapped in ``admin_view`` by the AdminSite."""
    _ensure_lab_admin(request)
    user = cast(User, request.user)
    has_device = services.has_confirmed_totp_device(user)
    if has_device and not services.is_verified(user):
        return redirect(services.get_mfa_url(user, request.get_full_path()))

    if request.method == "POST" and has_device:
        action = request.POST.get("action")
        if action == "remove_devices":
            services.remove_devices(user)
            logger.warning("MFA devices removed by user %s", user.pk)
            messages.success(
                request, _("Your two-factor authentication device has been removed.")
            )
            if services.is_mfa_required(user):
                return redirect("mfa_setup")
            return redirect("admin:account_security")

    device = services.get_confirmed_totp_device(user) if has_device else None
    return render(
        request,
        "euphro_auth/mfa/account_security.html",
        {
            **admin.site.each_context(request),
            "title": _("Account security"),
            "device": device,
        },
    )
