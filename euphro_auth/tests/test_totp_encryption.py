import pytest
from allauth.mfa.models import Authenticator
from allauth.mfa.totp.internal.auth import TOTP, generate_totp_secret
from cryptography.fernet import Fernet
from django.core.management import call_command

from euphro_auth.checks import check_totp_encryption_keys
from euphro_auth.mfa.adapter import MFAAdapter

from .factories import LabAdminUserFactory
from .test_mfa import totp_code

pytestmark = pytest.mark.django_db


@pytest.fixture(name="first_key")
def first_key_fixture(settings):
    key = Fernet.generate_key().decode()
    settings.MFA_TOTP_ENCRYPTION_KEYS = [key]
    return key


@pytest.mark.usefixtures("first_key")
def test_totp_secret_is_stored_encrypted_and_still_validates_codes():
    secret = generate_totp_secret()
    totp = TOTP.activate(LabAdminUserFactory(), secret)
    stored = Authenticator.objects.get().data["secret"]
    assert stored.startswith("fernet:")
    assert secret not in stored
    assert totp.validate_code(totp_code(secret))


@pytest.mark.usefixtures("first_key")
def test_unencrypted_secret_is_refused():
    with pytest.raises(ValueError):
        MFAAdapter().decrypt(generate_totp_secret())


def test_keys_rotate(settings, first_key):
    secret = generate_totp_secret()
    totp = TOTP.activate(LabAdminUserFactory(), secret)
    new_key = Fernet.generate_key().decode()
    settings.MFA_TOTP_ENCRYPTION_KEYS = [new_key, first_key]
    assert totp.validate_code(totp_code(secret, -1))

    call_command("rotate_totp_keys")

    settings.MFA_TOTP_ENCRYPTION_KEYS = [new_key]
    totp.instance.refresh_from_db()
    assert totp.validate_code(totp_code(secret, 1))


@pytest.mark.parametrize(
    "keys, error_id",
    [([], "euphro_auth.E001"), (["not-a-key"], "euphro_auth.E002")],
)
def test_missing_or_invalid_keys_fail_the_system_check(settings, keys, error_id):
    settings.MFA_TOTP_ENCRYPTION_KEYS = keys
    assert [error.id for error in check_totp_encryption_keys(None)] == [error_id]


@pytest.mark.usefixtures("first_key")
def test_valid_keys_pass_the_system_check():
    assert not check_totp_encryption_keys(None)
