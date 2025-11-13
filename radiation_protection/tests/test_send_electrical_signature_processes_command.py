from io import StringIO
from unittest import mock

import pytest
from django.core.management import call_command

from lab.tests import factories as lab_factories
from radiation_protection.models import ElectricalSignatureProcess
from radiation_protection.tests import factories as radiation_factories


@pytest.fixture(name="risk_prevention_plan")
def risk_prevention_plan_fixture():
    """Create a risk prevention plan that hasn't been sent yet."""
    user = lab_factories.StaffUserFactory()
    admin = lab_factories.StaffUserFactory()
    project = lab_factories.ProjectFactory(admin=admin)
    run = lab_factories.RunFactory(project=project)
    institution = lab_factories.InstitutionFactory()
    employer = lab_factories.EmployerFactory()

    participation = project.participation_set.create(
        user=user, institution=institution, employer=employer
    )

    return radiation_factories.RiskPreventionPlanFactory(
        participation=participation,
        run=run,
        risk_advisor_notification_sent=False,
    )


@pytest.mark.django_db
@mock.patch(
    "radiation_protection.management.commands.send_electrical_signature_processes.start_electrical_signature_processes"  # pylint: disable=line-too-long
)
def test_send_electrical_signature_processes_command(
    mock_start_processes, risk_prevention_plan, settings
):
    """Test the send_electrical_signature_processes management command."""
    settings.RADIATION_PROTECTION_RISK_ADVISOR_EMAIL = "advisor@example.com"
    settings.RADIATION_PROTECTION_RISK_ADVISOR_FULLNAME = "John Advisor"

    # Mock the electrical signature processes that will be created
    mock_process_1 = mock.Mock(spec=ElectricalSignatureProcess)
    mock_process_1.__str__ = mock.Mock(return_value="Process 1")
    mock_process_2 = mock.Mock(spec=ElectricalSignatureProcess)
    mock_process_2.__str__ = mock.Mock(return_value="Process 2")
    mock_start_processes.return_value = [mock_process_1, mock_process_2]

    out = StringIO()
    call_command("send_electrical_signature_processes", stdout=out)

    # Verify the command output
    output = out.getvalue()
    assert "Sending documents to sign" in output
    assert "Found 1 risk prevention plans to process" in output
    assert "Started electrical signature process" in output

    # Verify start_electrical_signature_processes was called
    mock_start_processes.assert_called_once_with(risk_prevention_plan)

    # Verify the plan was marked as sent
    risk_prevention_plan.refresh_from_db()
    assert risk_prevention_plan.risk_advisor_notification_sent is True


@pytest.mark.django_db
@mock.patch(
    "radiation_protection.management.commands.send_electrical_signature_processes.start_electrical_signature_processes"  # pylint: disable=line-too-long
)
def test_send_electrical_signature_processes_command_no_plans(
    mock_start_processes, settings
):
    """Test the command when there are no plans to process."""
    settings.RADIATION_PROTECTION_RISK_ADVISOR_EMAIL = "advisor@example.com"
    settings.RADIATION_PROTECTION_RISK_ADVISOR_FULLNAME = "John Advisor"

    out = StringIO()
    call_command("send_electrical_signature_processes", stdout=out)

    output = out.getvalue()
    assert "Found 0 risk prevention plans to process" in output
    mock_start_processes.assert_not_called()


@pytest.mark.django_db
@mock.patch(
    "radiation_protection.management.commands.send_electrical_signature_processes.start_electrical_signature_processes"  # pylint: disable=line-too-long
)
def test_send_electrical_signature_processes_command_already_sent(
    mock_start_processes, settings
):
    """Test the command skips plans that were already sent."""
    settings.RADIATION_PROTECTION_RISK_ADVISOR_EMAIL = "advisor@example.com"
    settings.RADIATION_PROTECTION_RISK_ADVISOR_FULLNAME = "John Advisor"

    user = lab_factories.StaffUserFactory()
    admin = lab_factories.StaffUserFactory()
    project = lab_factories.ProjectFactory(admin=admin)
    run = lab_factories.RunFactory(project=project)
    institution = lab_factories.InstitutionFactory()
    employer = lab_factories.EmployerFactory()

    participation = project.participation_set.create(
        user=user, institution=institution, employer=employer
    )

    # Create a plan that was already sent
    radiation_factories.RiskPreventionPlanFactory(
        participation=participation,
        run=run,
        risk_advisor_notification_sent=True,
    )

    out = StringIO()
    call_command("send_electrical_signature_processes", stdout=out)

    output = out.getvalue()
    assert "Found 0 risk prevention plans to process" in output
    mock_start_processes.assert_not_called()


@pytest.mark.django_db
@mock.patch(
    "radiation_protection.management.commands.send_electrical_signature_processes.start_electrical_signature_processes"  # pylint: disable=line-too-long
)
def test_send_electrical_signature_processes_command_multiple_plans(
    mock_start_processes, settings
):
    """Test the command with multiple plans to process."""
    settings.RADIATION_PROTECTION_RISK_ADVISOR_EMAIL = "advisor@example.com"
    settings.RADIATION_PROTECTION_RISK_ADVISOR_FULLNAME = "John Advisor"

    # Create multiple plans
    plans = []
    for _ in range(3):
        user = lab_factories.StaffUserFactory()
        admin = lab_factories.StaffUserFactory()
        project = lab_factories.ProjectFactory(admin=admin)
        run = lab_factories.RunFactory(project=project)
        institution = lab_factories.InstitutionFactory()
        employer = lab_factories.EmployerFactory()

        participation = project.participation_set.create(
            user=user, institution=institution, employer=employer
        )

        plan = radiation_factories.RiskPreventionPlanFactory(
            participation=participation,
            run=run,
            risk_advisor_notification_sent=False,
        )
        plans.append(plan)

    mock_process = mock.Mock(spec=ElectricalSignatureProcess)
    mock_process.__str__ = mock.Mock(return_value="Process")
    mock_start_processes.return_value = [mock_process, mock_process]

    out = StringIO()
    call_command("send_electrical_signature_processes", stdout=out)

    output = out.getvalue()
    assert "Found 3 risk prevention plans to process" in output

    # Verify start_electrical_signature_processes was called for each plan
    assert mock_start_processes.call_count == 3

    # Verify all plans were marked as sent
    for plan in plans:
        plan.refresh_from_db()
        assert plan.risk_advisor_notification_sent is True
