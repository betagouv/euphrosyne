import logging
import time

import pytest
from allauth.mfa import app_settings as mfa_settings
from allauth.mfa.models import Authenticator
from allauth.mfa.totp.internal.auth import (
    TOTP,
    format_hotp_value,
    generate_totp_secret,
    hotp_value,
)
from allauth.socialaccount.models import SocialAccount
from django.contrib import auth
from django.contrib.admin.models import LogEntry
from django.core import mail
from django.core.management import CommandError, call_command
from django.test import Client
from django.urls import reverse

from euphro_auth.mfa.adapter import MFAAdapter
from euphro_auth.mfa.conf import parse_mfa_admin_required, warn_if_mfa_disabled
from orcid_oauth.tests.helpers import orcid_callback, start_orcid_login

from .factories import LabAdminUserFactory, StaffUserFactory

pytestmark = pytest.mark.django_db

PASSWORD = "T8!vQ2#rM6@zL9$p"
PROJECTS_URL = "/lab/project/"
ACTIVATE_URL = "/accounts/2fa/totp/activate/"
LOGIN_URL = "/accounts/login/"


@pytest.fixture(autouse=True)
def mfa_required(settings):
    settings.MFA_ADMIN_REQUIRED = True
    settings.STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
        },
    }


def totp_code(secret: str, offset: int = 0) -> str:
    """One of the three codes accepted now (tolerance of one period). allauth
    refuses a code already used, so successive verifications use offsets."""
    counter = int(time.time()) // mfa_settings.TOTP_PERIOD + offset
    return format_hotp_value(hotp_value(secret, counter))


def enroll(user) -> str:
    secret = generate_totp_secret()
    TOTP.activate(user, secret)
    return secret


@pytest.fixture(name="admin_user")
def admin_user_fixture():
    user = LabAdminUserFactory()
    user.set_password(PASSWORD)
    user.save()
    return user


def password_login(client: Client, user, **data):
    return client.post(
        reverse("account_login"),
        {"login": user.email, "password": PASSWORD, **data},
    )


def reauthenticate(client: Client) -> None:
    """allauth asks for the password again before enrollment."""
    client.post(reverse("account_reauthenticate"), {"password": PASSWORD})


def sign_in(client: Client, user, secret: str, offset: int = 0) -> None:
    """Sign in with the password and a code: a verified session."""
    assert password_login(client, user).url == reverse("mfa_authenticate")
    client.post(reverse("mfa_authenticate"), {"code": totp_code(secret, offset)})
    assert auth.get_user(client).pk == user.pk


@pytest.fixture(name="verified_client")
def verified_client_fixture(client, admin_user):
    secret = enroll(admin_user)
    sign_in(client, admin_user, secret)
    client.secret = secret
    return client


def assert_mfa_gate(client: Client, url: str, expected: str) -> None:
    response = client.get(url)
    assert response.status_code == 302
    assert response.headers["Location"].startswith(expected)


# Enrollment right after sign-in (D-MFA01)


def test_admin_without_factor_must_enroll_after_password_login(client, admin_user):
    assert password_login(client, admin_user).status_code == 302
    assert auth.get_user(client).pk == admin_user.pk

    assert_mfa_gate(client, PROJECTS_URL, ACTIVATE_URL)
    # The password just entered is enough: no second prompt.
    response = client.get(ACTIVATE_URL)
    assert response.status_code == 200
    totp_url = response.context["totp_url"]
    assert totp_url.startswith("otpauth://totp/")
    assert "issuer=Euphrosyne" in totp_url
    assert response.context["totp_svg_data_uri"].startswith("data:image/svg+xml")
    assert response.context["form"].secret in response.content.decode()


def test_enrollment_asks_for_the_password_again_after_the_timeout(
    client, admin_user, settings
):
    password_login(client, admin_user)
    settings.ACCOUNT_REAUTHENTICATION_TIMEOUT = 0
    assert_mfa_gate(client, ACTIVATE_URL, reverse("account_reauthenticate"))


def test_enrollment_keeps_the_secret_shown_when_the_page_is_requested_again(
    client, admin_user
):
    password_login(client, admin_user)
    secret = client.get(ACTIVATE_URL).context["form"].secret
    # The browser's favicon request is redirected to the enrollment page.
    assert_mfa_gate(client, "/favicon.ico", ACTIVATE_URL)
    assert client.get(f"{ACTIVATE_URL}?next=/favicon.ico").context["form"].secret == (
        secret
    )

    response = client.post(ACTIVATE_URL, {"code": totp_code(secret)})

    assert response.status_code == 302
    assert Authenticator.objects.filter(user=admin_user, type="totp").exists()


@pytest.mark.parametrize("path", [PROJECTS_URL, "/", "/accounts/2fa/"])
def test_unverified_admin_pages_redirect_to_enrollment(client, admin_user, path):
    client.force_login(admin_user)
    assert_mfa_gate(client, path, f"{ACTIVATE_URL}?next=")


def test_unverified_admin_api_calls_get_a_json_403(client, admin_user):
    client.force_login(admin_user)
    response = client.post("/api/auth/token/")
    assert response.status_code == 403
    assert response.json() == {
        "detail": "L’authentification à deux facteurs est requise.",
        "code": "mfa_required",
        "redirect_url": ACTIVATE_URL,
    }


def test_unverified_admin_can_reach_cgu_and_log_out(client, admin_user):
    client.force_login(admin_user)
    assert client.get(reverse("cgu_acceptance")).status_code == 200
    assert client.get(reverse("static_cgu")).status_code == 200
    assert client.post(reverse("admin:logout")).status_code == 302
    assert not auth.get_user(client).is_authenticated


@pytest.mark.parametrize(
    "language, subject, message",
    [
        (
            "en",
            "[Euphrosyne] Authenticator App Activated",
            "Two-factor authentication is enabled. "
            "Sign in again with a code from your app.",
        ),
        (
            "fr",
            "[Euphrosyne] Application d'authentification activée",
            "L’authentification à deux facteurs est activée. "
            "Reconnectez-vous avec un code de votre application.",
        ),
    ],
)
# Transactional: allauth sends the notice once the factor is committed.
@pytest.mark.django_db(transaction=True)
def test_enrollment_signs_out_and_informs_owner(admin_user, language, subject, message):
    # The preferred language follows the browser's (UserLanguageMiddleware).
    client = Client(headers={"accept-language": language})
    password_login(client, admin_user)
    secret = client.get(ACTIVATE_URL).context["form"].secret

    response = client.post(ACTIVATE_URL, {"code": totp_code(secret)})

    assert response.url == LOGIN_URL
    assert not auth.get_user(client).is_authenticated
    assert Authenticator.objects.filter(user=admin_user, type="totp").exists()
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == [admin_user.email]
    assert mail.outbox[0].subject == subject
    # The notice gives the site, not the client IP address (the hosting
    # router's).
    assert "testserver" in mail.outbox[0].body
    assert "127.0.0.1" not in mail.outbox[0].body
    assert message in client.get(LOGIN_URL).content.decode()
    # The code just used for enrollment is refused: sign in with the next one.
    sign_in(client, admin_user, secret, offset=1)
    assert client.get(PROJECTS_URL).status_code == 200


# Verification


def test_admin_with_factor_gives_a_code_before_being_signed_in(
    client, admin_user, caplog
):
    secret = enroll(admin_user)
    response = password_login(client, admin_user)
    assert response.url == reverse("mfa_authenticate")
    assert not auth.get_user(client).is_authenticated

    with caplog.at_level(logging.INFO, logger="euphro_auth.mfa.signals"):
        response = client.post(reverse("mfa_authenticate"), {"code": "000000"})
        assert response.status_code == 200
        assert not auth.get_user(client).is_authenticated
        response = client.post(reverse("mfa_authenticate"), {"code": totp_code(secret)})
    assert response.status_code == 302
    assert auth.get_user(client).pk == admin_user.pk
    assert caplog.messages == [f"MFA code rejected for user {admin_user.pk} (sign-in)"]
    assert client.get(PROJECTS_URL).status_code == 200


def test_wrong_reauthentication_code_is_logged(verified_client, admin_user, caplog):
    with caplog.at_level(logging.WARNING, logger="euphro_auth.mfa.signals"):
        response = verified_client.post(
            reverse("mfa_reauthenticate"), {"code": "000000"}
        )
    assert response.status_code == 200
    assert caplog.messages == [
        f"MFA code rejected for user {admin_user.pk} (reauthentication)"
    ]


def test_codes_are_throttled_after_five_failures(client, admin_user):
    secret = enroll(admin_user)
    password_login(client, admin_user)
    for _ in range(5):
        client.post(reverse("mfa_authenticate"), {"code": "000000"})
    response = client.post(reverse("mfa_authenticate"), {"code": totp_code(secret)})
    assert response.status_code == 200
    assert not auth.get_user(client).is_authenticated


def test_a_code_cannot_be_used_twice(client, admin_user):
    secret = enroll(admin_user)
    code = totp_code(secret)
    password_login(client, admin_user)
    client.post(reverse("mfa_authenticate"), {"code": code})
    other = Client()
    password_login(other, admin_user)
    response = other.post(reverse("mfa_authenticate"), {"code": code})
    assert response.status_code == 200
    assert not auth.get_user(other).is_authenticated


def test_orcid_admin_without_password_enrolls_without_reauthentication(
    client, admin_user
):
    SocialAccount.objects.create(
        user=admin_user, provider="orcid", uid="0000-0002-1234-5678"
    )
    admin_user.set_unusable_password()
    admin_user.invitation_completed_at = admin_user.date_joined
    admin_user.save()
    start_orcid_login(client)
    orcid_callback(client)
    assert client.get(ACTIVATE_URL).status_code == 200


def test_orcid_sign_in_of_an_admin_requires_the_second_factor(client, admin_user):
    SocialAccount.objects.create(
        user=admin_user, provider="orcid", uid="0000-0002-1234-5678"
    )
    admin_user.invitation_completed_at = admin_user.date_joined
    admin_user.save()
    start_orcid_login(client)
    assert orcid_callback(client).url == "/"
    assert_mfa_gate(client, PROJECTS_URL, ACTIVATE_URL)

    secret = enroll(admin_user)
    other = Client()
    start_orcid_login(other)
    assert orcid_callback(other).url == reverse("mfa_authenticate")
    assert not auth.get_user(other).is_authenticated
    other.post(reverse("mfa_authenticate"), {"code": totp_code(secret)})
    assert other.get(PROJECTS_URL).status_code == 200


@pytest.mark.parametrize("path", [PROJECTS_URL, "/accounts/2fa/reauthenticate/"])
def test_session_signed_in_without_code_must_sign_in_again(client, admin_user, path):
    secret = enroll(admin_user)
    client.force_login(admin_user)

    response = client.get(path)

    assert response.url == f"{LOGIN_URL}?next={path.replace('/', '%2F')}"
    assert not auth.get_user(client).is_authenticated
    sign_in(client, admin_user, secret)
    assert client.get(PROJECTS_URL).status_code == 200


def test_api_call_of_a_session_signed_in_without_code_signs_it_out(client, admin_user):
    enroll(admin_user)
    client.force_login(admin_user)
    response = client.post("/api/auth/token/")
    assert response.status_code == 403
    assert response.json() == {
        "detail": "Reconnectez-vous avec un code de votre application.",
        "code": "mfa_required",
        "redirect_url": LOGIN_URL,
    }
    assert not auth.get_user(client).is_authenticated


def test_verified_session_stays_verified(verified_client):
    for _ in range(3):
        assert verified_client.get(PROJECTS_URL).status_code == 200
    assert verified_client.post("/api/auth/token/").status_code == 200


# Other users


def test_other_users_are_not_affected(client):
    user = StaffUserFactory()
    user.set_password(PASSWORD)
    user.save()
    assert password_login(client, user).status_code == 302
    assert client.get(PROJECTS_URL).status_code == 200
    for url in ("/accounts/2fa/", ACTIVATE_URL, "/accounts/2fa/reauthenticate/"):
        assert client.get(url).status_code == 403


# Account security page


def test_own_profile_links_to_the_account_security_page(verified_client, admin_user):
    link = f'href="{reverse("mfa_index")}"'
    own_profile = reverse("admin:euphro_auth_user_change", args=[admin_user.pk])
    assert link in verified_client.get(own_profile).content.decode()
    other_profile = reverse(
        "admin:euphro_auth_user_change", args=[StaffUserFactory().pk]
    )
    assert link not in verified_client.get(other_profile).content.decode()


def test_account_security_page_shows_the_factor(verified_client):
    response = verified_client.get(reverse("mfa_index"))
    assert response.status_code == 200
    assert response.context["authenticators"]["totp"]


def test_removing_the_factor_requires_setting_up_a_new_one(
    verified_client, admin_user, caplog
):
    other_client = Client()
    sign_in(other_client, admin_user, verified_client.secret, offset=1)
    # Removal asks for a fresh password or code, even right after sign-in.
    verified_client.post(reverse("account_reauthenticate"), {"password": PASSWORD})
    with caplog.at_level(logging.WARNING, logger="euphro_auth.mfa.views"):
        response = verified_client.post(reverse("mfa_deactivate_totp"))
    assert response.url == reverse("mfa_activate_totp")
    assert not Authenticator.objects.filter(user=admin_user).exists()
    assert f"MFA TOTP removed by user {admin_user.pk}" in caplog.messages
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == [admin_user.email]
    assert mail.outbox[0].subject == (
        "[Euphrosyne] Application d'authentification désactivée"
    )
    assert not auth.get_user(other_client).is_authenticated
    assert_mfa_gate(verified_client, PROJECTS_URL, ACTIVATE_URL)
    assert_mfa_gate(verified_client, reverse("mfa_index"), ACTIVATE_URL)


def test_removing_the_factor_needs_a_recent_code_or_password(
    verified_client, admin_user, settings
):
    settings.ACCOUNT_REAUTHENTICATION_TIMEOUT = 0
    response = verified_client.post(reverse("mfa_deactivate_totp"))
    assert response.status_code == 302
    assert response.url.startswith(reverse("account_reauthenticate"))
    assert Authenticator.objects.filter(user=admin_user).exists()
    assert not mail.outbox


def test_password_reset_keeps_the_factor(client, admin_user):
    enroll(admin_user)
    client.post(reverse("account_reset_password"), {"email": admin_user.email})
    assert len(mail.outbox) == 1
    assert Authenticator.objects.filter(user=admin_user).exists()


# Recovery through a superuser (R30)


def test_superuser_resets_a_factor_from_the_user_admin(verified_client, admin_user):
    admin_user.is_superuser = True
    admin_user.save()
    target = LabAdminUserFactory()
    target.set_password(PASSWORD)
    target.save()
    target_secret = enroll(target)
    target_client = Client()
    sign_in(target_client, target, target_secret)
    assert target_client.get(PROJECTS_URL).status_code == 200

    verified_client.post(
        reverse("admin:euphro_auth_user_changelist"),
        {"action": "reset_mfa_devices", "_selected_action": [target.pk]},
    )

    assert not Authenticator.objects.filter(user=target).exists()
    assert LogEntry.objects.filter(
        user=admin_user,
        object_id=str(target.pk),
        change_message="Reset two-factor authentication devices",
    ).exists()
    # The target is signed out everywhere and sets up a new factor at sign-in.
    assert not auth.get_user(target_client).is_authenticated


def test_reset_action_is_reserved_to_superusers(verified_client):
    target = LabAdminUserFactory()
    enroll(target)
    response = verified_client.get(reverse("admin:euphro_auth_user_changelist"))
    assert "reset_mfa_devices" not in response.content.decode()
    verified_client.post(
        reverse("admin:euphro_auth_user_changelist"),
        {"action": "reset_mfa_devices", "_selected_action": [target.pk]},
    )
    assert Authenticator.objects.filter(user=target).exists()


def test_reset_mfa_command(admin_user, caplog):
    enroll(admin_user)
    with caplog.at_level(logging.WARNING):
        call_command("reset_mfa", admin_user.email.upper())
    assert not Authenticator.objects.filter(user=admin_user).exists()
    assert (
        f"MFA devices of user {admin_user.pk} removed with reset_mfa" in caplog.messages
    )
    with pytest.raises(CommandError):
        call_command("reset_mfa", admin_user.email)
    with pytest.raises(CommandError):
        call_command("reset_mfa", "unknown@example.com")


def test_authenticators_are_not_editable_in_the_admin(verified_client, admin_user):
    admin_user.is_superuser = True
    admin_user.save()
    response = verified_client.get("/mfa/authenticator/")
    assert response.status_code == 404


# Impersonation


def test_impersonated_users_cannot_reach_the_mfa_pages(verified_client, admin_user):
    admin_user.is_superuser = True
    admin_user.save()
    target = StaffUserFactory()
    verified_client.post(
        reverse("admin:euphro_auth_user_changelist"),
        {"action": "impersonate_selected_user", "_selected_action": [target.pk]},
    )
    assert auth.get_user(verified_client).pk == target.pk
    assert verified_client.get(PROJECTS_URL).status_code == 200
    for url in ("/accounts/2fa/", ACTIVATE_URL):
        assert verified_client.get(url).status_code == 403


# Kill switch (rollback only)


@pytest.mark.parametrize(
    "value, required",
    [
        (None, True),
        ("", True),
        ("1", True),
        ("true", True),
        ("disabled", True),
        ("0", False),
        ("false", False),
        (" No ", False),
        ("OFF", False),
    ],
)
def test_kill_switch_only_accepts_explicit_false_values(value, required):
    assert parse_mfa_admin_required(value) is required


def test_kill_switch_off_disables_mfa_with_a_warning(
    client, admin_user, caplog, settings
):
    settings.MFA_ADMIN_REQUIRED = False
    enroll(admin_user)
    with caplog.at_level(logging.WARNING, logger="euphro_auth.mfa.conf"):
        warn_if_mfa_disabled()
    assert "MFA_ADMIN_REQUIRED is off" in caplog.text
    assert password_login(client, admin_user).url == "/"
    assert client.get(PROJECTS_URL).status_code == 200


# Encryption of TOTP secrets


def test_totp_secret_is_stored_encrypted_and_still_validates_codes(admin_user):
    secret = generate_totp_secret()
    totp = TOTP.activate(admin_user, secret)
    stored = Authenticator.objects.get().data["secret"]
    assert stored.startswith("fernet:")
    assert secret not in stored
    assert totp.validate_code(totp_code(secret))


def test_unencrypted_secret_is_refused():
    with pytest.raises(ValueError):
        MFAAdapter().decrypt(generate_totp_secret())


def test_secret_key_change_sends_administrators_back_to_enrollment(
    client, admin_user, settings, caplog
):
    enroll(admin_user)
    settings.SECRET_KEY = "another-secret-key"

    with caplog.at_level(logging.WARNING, logger="euphro_auth.mfa.services"):
        assert password_login(client, admin_user).status_code == 302
    assert auth.get_user(client).pk == admin_user.pk
    assert not Authenticator.objects.exists()
    assert (
        f"MFA TOTP of user {admin_user.pk} removed: its secret cannot be "
        "decrypted with the current SECRET_KEY" in caplog.messages
    )
    assert_mfa_gate(client, PROJECTS_URL, ACTIVATE_URL)
