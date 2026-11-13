import pytest
from django.core.management import CommandError, call_command
from django_otp.plugins.otp_totp.models import TOTPDevice

from .factories import LabAdminUserFactory

pytestmark = pytest.mark.django_db


def test_reset_mfa_removes_devices_of_the_user():
    user = LabAdminUserFactory()
    other = LabAdminUserFactory()
    for owner in (user, other):
        TOTPDevice.objects.create(user=owner, name="Authenticator", confirmed=True)

    call_command("reset_mfa", user.email.upper())

    assert not TOTPDevice.objects.filter(user=user).exists()
    assert TOTPDevice.objects.filter(user=other).exists()


def test_reset_mfa_unknown_email():
    with pytest.raises(CommandError):
        call_command("reset_mfa", "nobody@example.com")


def test_reset_mfa_user_without_device():
    user = LabAdminUserFactory()
    with pytest.raises(CommandError):
        call_command("reset_mfa", user.email)
