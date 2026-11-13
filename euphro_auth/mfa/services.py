"""Multi-factor authentication (TOTP) for lab administrators."""

import logging
import textwrap
from base64 import b32encode

import segno
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.db import transaction
from django.http import HttpRequest
from django.middleware.csrf import rotate_token
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme, urlencode
from django_otp import login as otp_login
from django_otp import verify_token
from django_otp.models import Device
from django_otp.plugins.otp_totp.models import TOTPDevice

from lab.permissions import is_lab_admin

from ..models import User

logger = logging.getLogger(__name__)

TOTP_DEVICE_NAME = "Authenticator"
TOTP_CODE_LENGTH = 6


def is_mfa_required(user: User | AnonymousUser) -> bool:
    """Whether MFA is enforced for this (session) user."""
    return bool(
        settings.MFA_ADMIN_REQUIRED and user.is_authenticated and is_lab_admin(user)
    )


def is_verified(user: User | AnonymousUser) -> bool:
    """Whether the session has been verified with a second factor.

    ``is_verified`` is installed on the user by django-otp's OTPMiddleware.
    """
    verified = getattr(user, "is_verified", None)
    return bool(user.is_authenticated and verified and verified())


def get_confirmed_totp_device(user: User) -> TOTPDevice | None:
    return (
        TOTPDevice.objects.devices_for_user(user, confirmed=True).order_by("pk").first()
    )


def has_confirmed_totp_device(user: User) -> bool:
    return TOTPDevice.objects.devices_for_user(user, confirmed=True).exists()


def get_or_create_pending_totp_device(user: User) -> TOTPDevice:
    """Return the unconfirmed TOTP device being enrolled, creating it if needed.

    Reusing it keeps the QR code stable when the enrollment page is reloaded.
    """
    device = (
        TOTPDevice.objects.devices_for_user(user, confirmed=False)
        .order_by("-pk")
        .first()
    )
    if device is None:
        device = TOTPDevice.objects.create(
            user=user, name=TOTP_DEVICE_NAME, confirmed=False
        )
    return device


def get_totp_secret(device: TOTPDevice) -> str:
    """Base32 secret, grouped by four characters for manual entry."""
    secret = b32encode(device.bin_key).decode("ascii")
    return " ".join(textwrap.wrap(secret, 4))


def get_totp_qr_code_svg(device: TOTPDevice) -> str:
    """Inline SVG QR code of the otpauth:// provisioning URI."""
    return segno.make(device.config_url, error="m").svg_inline(
        scale=5, dark="#000000", light="#ffffff"
    )


def confirm_totp_enrollment(user: User, device: TOTPDevice, code: str) -> bool:
    """Confirm a pending TOTP device with a first code."""
    code = _normalize_code(code)
    if device.user_id != user.pk or device.confirmed:
        return False
    with transaction.atomic():
        if not (len(code) == TOTP_CODE_LENGTH and device.verify_token(code)):
            logger.warning(
                "MFA enrollment code rejected for user %s (consecutive failures: %s)",
                user.pk,
                _failure_count([device]),
            )
            return False
        device.confirmed = True
        device.save(update_fields=["confirmed"])
        TOTPDevice.objects.filter(user=user).exclude(pk=device.pk).delete()
    logger.info("MFA TOTP device enrolled for user %s", user.pk)
    return True


def verify_code(user: User, code: str) -> Device | None:
    """Check a TOTP code against the user's confirmed authenticator devices.

    django-otp throttling applies: failures increase an exponential delay during
    which every code is refused.
    """
    code = _normalize_code(code)
    devices = list(TOTPDevice.objects.devices_for_user(user, confirmed=True))

    throttled = False
    if code.isdigit() and len(code) == TOTP_CODE_LENGTH:
        for device in devices:
            throttled = throttled or not device.verify_is_allowed()[0]
            verified = verify_token(user, device.persistent_id, code)
            if verified is not None:
                logger.info("MFA verification succeeded for user %s", user.pk)
                return verified

    logger.warning(
        "MFA verification failed for user %s (%sconsecutive failures: %s)",
        user.pk,
        "throttled, " if throttled else "",
        _failure_count(devices),
    )
    return None


def _failure_count(devices: list[TOTPDevice]) -> int:
    """Highest consecutive failure count among the devices, as stored by
    django-otp's throttling (reset on success)."""
    counts = [0]
    for device in devices:
        device.refresh_from_db(fields=["throttling_failure_count"])
        counts.append(device.throttling_failure_count)  # type: ignore[attr-defined]
    return max(counts)


def mark_session_verified(request: HttpRequest, device: Device) -> None:
    """Persist the verifying device in the session and renew session keys."""
    otp_login(request, device)
    request.session.cycle_key()
    rotate_token(request)


def remove_devices(user: User) -> int:
    """Delete every authenticator device of a user."""
    count, _ = TOTPDevice.objects.filter(user=user).delete()
    return count


def get_safe_next_url(request: HttpRequest, default: str = "/") -> str:
    next_url = request.POST.get("next") or request.GET.get("next") or ""
    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return next_url
    return default


def get_mfa_url(user: User, next_url: str | None = None) -> str:
    """URL of the step the user must complete: verification or enrollment."""
    url = reverse(
        "mfa_verify" if has_confirmed_totp_device(user) else "mfa_setup",
    )
    if next_url:
        url += "?" + urlencode({"next": next_url})
    return url


def _normalize_code(code: str) -> str:
    return "".join((code or "").split())
