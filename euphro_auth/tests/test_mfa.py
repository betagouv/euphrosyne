import logging
import time
from unittest.mock import patch

import pytest
from django.contrib import auth
from django.contrib.admin.models import LogEntry
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.test import Client
from django.urls import include, path, reverse
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import gettext
from django_otp import DEVICE_ID_SESSION_KEY
from django_otp.oath import TOTP
from django_otp.plugins.otp_totp.models import TOTPDevice
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from social_django.models import UserSocialAuth

from euphro_auth.jwt.tokens import EuphroRefreshToken
from euphro_auth.mfa import services
from orcid_oauth.backends import ORCIDOAuth2

from .factories import LabAdminUserFactory, StaffUserFactory

pytestmark = pytest.mark.django_db

PASSWORD = "T8!vQ2#rM6@zL9$p"
PROJECTS_URL = "/lab/project/"


@pytest.fixture(autouse=True)
def mfa_required(settings):
    settings.MFA_ADMIN_REQUIRED = True
    settings.STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
        },
    }


def totp_code(device: TOTPDevice, offset_steps: int = 0) -> str:
    totp = TOTP(device.bin_key, device.step, device.t0, device.digits, device.drift)
    totp.time = time.time() + offset_steps * device.step
    return f"{totp.token():0{device.digits}d}"


def make_totp_device(user, confirmed=True) -> TOTPDevice:
    return TOTPDevice.objects.create(
        user=user, name="Authenticator", confirmed=confirmed
    )


def verify_session(client: Client, device) -> None:
    session = client.session
    session[DEVICE_ID_SESSION_KEY] = device.persistent_id
    session.save()


@pytest.fixture(name="admin_user")
def admin_user_fixture():
    return LabAdminUserFactory()


@pytest.fixture(name="admin_client")
def unverified_admin_client(client, admin_user):
    client.force_login(admin_user)
    return client


@pytest.fixture(name="verified_admin_client")
def verified_admin_client_fixture(client, admin_user):
    device = make_totp_device(admin_user)
    client.force_login(admin_user)
    verify_session(client, device)
    return client


# --- Middleware ------------------------------------------------------------


def test_unverified_admin_with_device_is_redirected_to_verify(admin_client, admin_user):
    make_totp_device(admin_user)
    response = admin_client.get(PROJECTS_URL)
    assert response.status_code == 302
    assert response.url == f"{reverse('mfa_verify')}?next=%2Flab%2Fproject%2F"


def test_unverified_admin_without_device_is_redirected_to_setup(admin_client):
    response = admin_client.get(PROJECTS_URL)
    assert response.status_code == 302
    assert response.url.startswith(reverse("mfa_setup") + "?next=")


def test_unconfirmed_device_does_not_count_as_enrolled(admin_client, admin_user):
    make_totp_device(admin_user, confirmed=False)
    response = admin_client.get(PROJECTS_URL)
    assert response.url.startswith(reverse("mfa_setup"))


def test_superuser_is_gated(client):
    client.force_login(StaffUserFactory(is_superuser=True))
    assert client.get(PROJECTS_URL).status_code == 302


def test_post_redirect_has_no_next(admin_client, admin_user):
    make_totp_device(admin_user)
    response = admin_client.post(PROJECTS_URL)
    assert response.url == reverse("mfa_verify")


def test_unverified_admin_api_request_gets_403_json(admin_client):
    response = admin_client.post("/api/auth/token/")
    assert response.status_code == 403
    assert response.json()["code"] == "mfa_required"


@pytest.mark.parametrize(
    "url",
    [
        "/mfa/verify/",
        "/mfa/setup/",
        "/jsi18n/",
        "/cgu-acceptance/",
    ],
)
def test_allowed_pages_for_unverified_admin(admin_client, admin_user, url):
    if url == "/mfa/verify/":
        make_totp_device(admin_user)
    assert admin_client.get(url).status_code == 200


def test_unverified_admin_can_log_out(admin_client):
    response = admin_client.post(reverse("admin:logout"))
    assert response.status_code in (200, 302)
    assert not auth.get_user(admin_client).is_authenticated


def test_verified_admin_is_not_gated(verified_admin_client):
    assert verified_admin_client.get(PROJECTS_URL).status_code == 200


def test_non_admin_is_not_affected(client):
    client.force_login(StaffUserFactory())
    assert client.get(PROJECTS_URL).status_code == 200
    assert client.post("/api/auth/token/").status_code == 200


def test_mfa_not_required_when_disabled(settings, admin_client):
    settings.MFA_ADMIN_REQUIRED = False
    assert admin_client.get(PROJECTS_URL).status_code == 200


def test_no_redirect_loop_with_cgu_acceptance(settings, admin_client, admin_user):
    settings.FORCE_LAST_CGU_ACCEPTANCE_DT = admin_user.cgu_accepted_at.replace(
        year=admin_user.cgu_accepted_at.year + 1
    )
    make_totp_device(admin_user)
    response = admin_client.get(PROJECTS_URL)
    assert response.url.startswith(reverse("mfa_verify"))
    response = admin_client.get(response.url)
    assert response.url == reverse("cgu_acceptance")
    assert admin_client.get(response.url).status_code == 200


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def jwt_probe_view(_request):
    return Response({"status": "ok"})


urlpatterns = [
    path("api/mfa-jwt-probe/", jwt_probe_view),
    path("", include("euphrosyne.urls")),
]


def test_jwt_authenticated_admin_request_is_not_gated(settings, client, admin_user):
    settings.ROOT_URLCONF = __name__
    access = EuphroRefreshToken.for_user(admin_user).access_token
    response = client.get("/api/mfa-jwt-probe/", HTTP_AUTHORIZATION=f"Bearer {access}")
    assert response.status_code == 200


def test_orcid_login_requires_mfa(settings, client, admin_user):
    settings.SOCIAL_AUTH_ORCID_KEY = "client-id"
    settings.SOCIAL_AUTH_ORCID_SECRET = "client-secret"
    admin_user.invitation_completed_at = timezone.now()
    admin_user.save()
    make_totp_device(admin_user)
    uid = "0000-0002-1234-5678"
    UserSocialAuth.objects.create(
        user=admin_user, provider="orcid", uid=uid, id_key="orcid"
    )
    assert client.post(reverse("social:begin", args=("orcid",))).status_code == 302
    state = next(reversed(client.session["orcid_oauth2_transaction_index"]))
    with (
        patch.object(
            ORCIDOAuth2,
            "request_access_token",
            return_value={"orcid": uid, "access_token": "token"},
        ),
        patch.object(
            ORCIDOAuth2,
            "user_data",
            return_value={
                "orcid-identifier": {"path": uid},
                "person": {"name": {}, "emails": {"email": []}},
            },
        ),
    ):
        response = client.get(
            reverse("social:complete", args=("orcid",)),
            {"state": state, "code": "valid-code"},
        )
    assert auth.get_user(client).pk == admin_user.pk
    response = client.get(response.url)
    assert response.status_code == 302
    assert response.url.startswith(reverse("mfa_verify"))


def test_password_login_requires_mfa(client):
    user = LabAdminUserFactory()
    user.set_password(PASSWORD)
    user.save()
    response = client.post(
        reverse("admin:login"),
        {"username": user.email, "password": PASSWORD},
        follow=True,
    )
    assert response.redirect_chain[-1][0].startswith(reverse("mfa_setup"))


# --- Verification ----------------------------------------------------------


def test_verify_with_totp_code(admin_client, admin_user, caplog):
    device = make_totp_device(admin_user)
    with caplog.at_level(logging.INFO, logger="euphro_auth.mfa.services"):
        response = admin_client.post(
            reverse("mfa_verify"), {"code": totp_code(device), "next": PROJECTS_URL}
        )
    assert response.status_code == 302
    assert response.url == PROJECTS_URL
    assert admin_client.session[DEVICE_ID_SESSION_KEY] == device.persistent_id
    assert admin_client.get(PROJECTS_URL).status_code == 200
    assert "MFA verification succeeded" in caplog.text


def test_verify_rejects_unsafe_next(admin_client, admin_user):
    device = make_totp_device(admin_user)
    response = admin_client.post(
        reverse("mfa_verify"),
        {"code": totp_code(device), "next": "https://evil.example.com/"},
    )
    assert response.url == "/"


def test_verify_failure_shows_generic_error_and_logs(admin_client, admin_user, caplog):
    device = make_totp_device(admin_user)
    with caplog.at_level(logging.WARNING, logger="euphro_auth.mfa.services"):
        response = admin_client.post(
            reverse("mfa_verify"), {"code": totp_code(device, offset_steps=10)}
        )
    assert response.status_code == 200
    assert gettext("Invalid code. Please try again.") in response.content.decode()
    assert DEVICE_ID_SESSION_KEY not in admin_client.session
    assert "MFA verification failed" in caplog.text
    device.refresh_from_db()
    assert device.throttling_failure_count == 1


def test_repeated_failures_log_warning_with_user_and_count(
    admin_client, admin_user, caplog
):
    device = make_totp_device(admin_user)
    with caplog.at_level(logging.WARNING, logger="euphro_auth.mfa.services"):
        for _ in range(3):
            admin_client.post(reverse("mfa_verify"), {"code": "000000"})
    records = [r for r in caplog.records if "MFA verification failed" in r.message]
    assert len(records) == 3
    assert all(r.levelno == logging.WARNING for r in records)
    assert f"user {admin_user.pk} " in records[-1].getMessage()
    # Attempts during the back-off delay are refused without counting.
    assert "consecutive failures: 1" in records[-1].getMessage()
    device.refresh_from_db()
    assert device.throttling_failure_count == 1


def test_verify_is_throttled_after_failure(admin_client, admin_user):
    device = make_totp_device(admin_user)
    admin_client.post(reverse("mfa_verify"), {"code": "000000"})
    # The valid code is refused during the back-off delay.
    response = admin_client.post(reverse("mfa_verify"), {"code": totp_code(device)})
    assert response.status_code == 200
    assert DEVICE_ID_SESSION_KEY not in admin_client.session


def test_verify_page_is_forbidden_for_non_admin(client):
    client.force_login(StaffUserFactory())
    assert client.get(reverse("mfa_verify")).status_code == 403


def test_verify_page_redirects_to_setup_without_device(admin_client):
    response = admin_client.get(reverse("mfa_verify"))
    assert response.url.startswith(reverse("mfa_setup"))


# --- Enrollment ------------------------------------------------------------


def test_setup_page_shows_qr_code_and_secret(admin_client, admin_user):
    response = admin_client.get(reverse("mfa_setup"))
    assert response.status_code == 200
    device = TOTPDevice.objects.get(user=admin_user)
    assert not device.confirmed
    content = response.content.decode()
    assert "<svg" in content
    assert services.get_totp_secret(device) in content
    assert "issuer=Euphrosyne" in device.config_url
    # Reloading keeps the same pending device.
    admin_client.get(reverse("mfa_setup"))
    assert TOTPDevice.objects.filter(user=admin_user).count() == 1


def test_setup_with_wrong_code(admin_client, admin_user):
    admin_client.get(reverse("mfa_setup"))
    device = TOTPDevice.objects.get(user=admin_user)
    response = admin_client.post(
        reverse("mfa_setup"), {"code": totp_code(device, offset_steps=10)}
    )
    assert response.status_code == 200
    device.refresh_from_db()
    assert not device.confirmed
    assert len(mail.outbox) == 0


def test_setup_confirms_device_and_redirects(admin_client, admin_user):
    admin_client.get(reverse("mfa_setup"))
    device = TOTPDevice.objects.get(user=admin_user)
    response = admin_client.post(
        reverse("mfa_setup"), {"code": totp_code(device), "next": PROJECTS_URL}
    )
    assert response.status_code == 302
    assert response.url == PROJECTS_URL
    device.refresh_from_db()
    assert device.confirmed
    assert admin_client.session[DEVICE_ID_SESSION_KEY] == device.persistent_id
    assert admin_client.get(PROJECTS_URL).status_code == 200
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == [admin_user.email]


def test_enrollment_email_uses_user_language(admin_client, admin_user):
    admin_user.preferred_language = "fr"
    admin_user.save()
    admin_client.get(reverse("mfa_setup"))
    device = TOTPDevice.objects.get(user=admin_user)
    admin_client.post(reverse("mfa_setup"), {"code": totp_code(device)})
    assert (
        mail.outbox[0].subject
        == "[Euphrosyne] Authentification à deux facteurs activée"
    )


def test_setup_refused_when_device_already_confirmed(admin_client, admin_user):
    make_totp_device(admin_user)
    response = admin_client.get(reverse("mfa_setup"))
    assert response.url.startswith(reverse("mfa_verify"))
    assert TOTPDevice.objects.filter(user=admin_user).count() == 1


# --- Account security page ---------------------------------------------------


def test_security_page_requires_verified_session(admin_client, admin_user):
    make_totp_device(admin_user)
    response = admin_client.get(reverse("admin:account_security"))
    assert response.url.startswith(reverse("mfa_verify"))


def test_security_page(verified_admin_client):
    response = verified_admin_client.get(reverse("admin:account_security"))
    assert response.status_code == 200


def test_remove_devices_sends_admin_to_setup(verified_admin_client, admin_user):
    response = verified_admin_client.post(
        reverse("admin:account_security"), {"action": "remove_devices"}
    )
    assert response.url == reverse("mfa_setup")
    assert not TOTPDevice.objects.filter(user=admin_user).exists()
    assert verified_admin_client.get(PROJECTS_URL).url.startswith(reverse("mfa_setup"))


# --- Superuser reset action ---------------------------------------------------


def test_superuser_can_reset_devices_of_another_user(client, admin_user, caplog):
    make_totp_device(admin_user)
    superuser = StaffUserFactory(is_superuser=True)
    client.force_login(superuser)
    verify_session(client, make_totp_device(superuser))
    with caplog.at_level(logging.WARNING, logger="euphro_auth.admin"):
        response = client.post(
            reverse("admin:euphro_auth_user_changelist"),
            {"action": "reset_mfa_devices", "_selected_action": [admin_user.pk]},
        )
    assert response.status_code == 302
    assert not TOTPDevice.objects.filter(user=admin_user).exists()
    assert TOTPDevice.objects.filter(user=superuser).exists()
    assert LogEntry.objects.filter(
        object_id=str(admin_user.pk),
        change_message="Reset two-factor authentication devices",
    ).exists()
    assert "MFA devices of user" in caplog.text


def test_lab_admin_cannot_reset_devices(verified_admin_client):
    other = LabAdminUserFactory()
    make_totp_device(other)
    verified_admin_client.post(
        reverse("admin:euphro_auth_user_changelist"),
        {"action": "reset_mfa_devices", "_selected_action": [other.pk]},
    )
    assert TOTPDevice.objects.filter(user=other).exists()


def test_otp_device_admin_is_not_registered():
    # pylint: disable=import-outside-toplevel
    from django.contrib import admin

    assert not admin.site.is_registered(TOTPDevice)


# --- Password reset ------------------------------------------------------------


def test_password_reset_keeps_devices(client, admin_user, settings):
    assert settings.PASSWORD_RESET_TIMEOUT == 3600
    make_totp_device(admin_user)
    uid = urlsafe_base64_encode(force_bytes(admin_user.pk))
    token = default_token_generator.make_token(admin_user)
    response = client.get(
        reverse("password_reset_confirm", args=(uid, token)), follow=True
    )
    new_password = "N3w!vQ2#rM6@zL9$pX"
    response = client.post(
        response.redirect_chain[-1][0],
        {"new_password1": new_password, "new_password2": new_password},
    )
    assert response.status_code == 302
    admin_user.refresh_from_db()
    assert admin_user.check_password(new_password)
    assert TOTPDevice.objects.filter(user=admin_user, confirmed=True).exists()
