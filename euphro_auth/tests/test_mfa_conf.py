import logging

import pytest

from euphro_auth.mfa.conf import parse_mfa_admin_required, warn_if_mfa_disabled


@pytest.mark.parametrize("value", ["0", "false", "FALSE", " No ", "off", "Off"])
def test_explicit_false_values_disable_mfa(value):
    assert parse_mfa_admin_required(value) is False


@pytest.mark.parametrize(
    "value", [None, "", "  ", "1", "true", "yes", "on", "flase", "disabled"]
)
def test_other_values_keep_mfa_enforced(value):
    assert parse_mfa_admin_required(value) is True


def test_warning_logged_when_mfa_disabled(settings, caplog):
    settings.MFA_ADMIN_REQUIRED = False
    with caplog.at_level(logging.WARNING, logger="euphro_auth.mfa.conf"):
        warn_if_mfa_disabled()
    assert "MFA_ADMIN_REQUIRED is off" in caplog.text


def test_no_warning_when_mfa_enforced(settings, caplog):
    settings.MFA_ADMIN_REQUIRED = True
    with caplog.at_level(logging.WARNING, logger="euphro_auth.mfa.conf"):
        warn_if_mfa_disabled()
    assert caplog.text == ""
