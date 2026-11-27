from io import StringIO
from unittest import mock

import pytest
from django.apps import apps
from django.core.management import call_command


@pytest.mark.django_db
@mock.patch("lab.management.commands.every_10_minutes_job.management.call_command")
def test_every_10_minutes_job_command(mock_call_command):
    """Test the every_10_minutes_job management command."""
    out = StringIO()
    call_command("every_10_minutes_job", stdout=out)

    # Verify the output
    output = out.getvalue()
    assert "Running commands..." in output

    # Verify send_notifications was called
    assert any(
        call[0][0] == "send_notifications" for call in mock_call_command.call_args_list
    )

    # Verify send_electrical_signature_processes was called
    # if radiation_protection is installed
    if apps.is_installed("radiation_protection"):
        assert any(
            call[0][0] == "send_electrical_signature_processes"
            for call in mock_call_command.call_args_list
        )


@pytest.mark.django_db
@mock.patch("lab.management.commands.every_10_minutes_job.management.call_command")
@mock.patch("lab.management.commands.every_10_minutes_job.apps.is_installed")
def test_every_10_minutes_job_command_without_radiation_protection(
    mock_is_installed, mock_call_command
):
    """Test the command when radiation_protection is not installed."""
    mock_is_installed.return_value = False

    out = StringIO()
    call_command("every_10_minutes_job", stdout=out)

    # Verify send_notifications was called
    assert any(
        call[0][0] == "send_notifications" for call in mock_call_command.call_args_list
    )

    # Verify send_electrical_signature_processes was NOT called
    assert not any(
        call[0][0] == "send_electrical_signature_processes"
        for call in mock_call_command.call_args_list
    )


@pytest.mark.django_db
@mock.patch("lab.management.commands.every_10_minutes_job.management.call_command")
def test_every_10_minutes_job_command_order(mock_call_command):
    """Test that commands are called in the correct order."""
    out = StringIO()
    call_command("every_10_minutes_job", stdout=out)

    # Get the order of commands called
    called_commands = [call[0][0] for call in mock_call_command.call_args_list]

    # Verify send_notifications is called first
    assert called_commands[0] == "send_notifications"

    # If radiation_protection is installed, verify the second command
    if apps.is_installed("radiation_protection"):
        assert called_commands[1] == "send_electrical_signature_processes"


@pytest.mark.django_db
@mock.patch("lab.management.commands.every_10_minutes_job.management.call_command")
@mock.patch("lab.management.commands.every_10_minutes_job.apps.is_installed")
def test_every_10_minutes_job_command_reconciles_lifecycle_operations(
    mock_is_installed, mock_call_command
):
    """Stale lifecycle operations are reconciled when data_management is installed."""
    mock_is_installed.side_effect = lambda app: app == "data_management"

    call_command("every_10_minutes_job", stdout=StringIO())

    called_commands = [call[0][0] for call in mock_call_command.call_args_list]
    assert called_commands == ["send_notifications", "reconcile_lifecycle_operations"]


@pytest.mark.django_db
@mock.patch("lab.management.commands.every_10_minutes_job.management.call_command")
@mock.patch("lab.management.commands.every_10_minutes_job.apps.is_installed")
def test_every_10_minutes_job_command_without_data_management(
    mock_is_installed, mock_call_command
):
    mock_is_installed.return_value = False

    call_command("every_10_minutes_job", stdout=StringIO())

    assert not any(
        call[0][0] == "reconcile_lifecycle_operations"
        for call in mock_call_command.call_args_list
    )
