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


@pytest.fixture(autouse=True)
def radiation_protection_settings():
    with (
        mock.patch(
            "radiation_protection.electrical_signature.electrical_signature."
            "app_settings.RADIATION_PROTECTION_RISK_ADVISOR_EMAIL",
            "advisor@example.com",
        ),
        mock.patch(
            "radiation_protection.electrical_signature.electrical_signature."
            "app_settings.RADIATION_PROTECTION_RISK_ADVISOR_FULLNAME",
            "John Advisor",
        ),
    ):
        yield


@pytest.mark.django_db
@mock.patch(
    "radiation_protection.management.commands.send_electrical_signature_processes.start_electrical_signature_processes"  # pylint: disable=line-too-long
)
def test_send_electrical_signature_processes_command(
    mock_start_processes, risk_prevention_plan
):
    """Test the send_electrical_signature_processes management command."""
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
def test_send_electrical_signature_processes_command_skips_exempt(
    mock_start_processes,
):
    """Test the command skips plans marked as electrical signature exempt."""
    user = lab_factories.StaffUserFactory()
    admin = lab_factories.StaffUserFactory()
    project = lab_factories.ProjectFactory(admin=admin)
    run_1 = lab_factories.RunFactory(project=project)
    run_2 = lab_factories.RunFactory(project=project)
    institution = lab_factories.InstitutionFactory()
    employer = lab_factories.EmployerFactory()

    participation = project.participation_set.create(
        user=user, institution=institution, employer=employer
    )

    exempt_plan = radiation_factories.RiskPreventionPlanFactory(
        participation=participation,
        run=run_1,
        risk_advisor_notification_sent=False,
        electrical_signature_exempt=True,
    )
    non_exempt_plan = radiation_factories.RiskPreventionPlanFactory(
        participation=participation,
        run=run_2,
        risk_advisor_notification_sent=False,
        electrical_signature_exempt=False,
    )

    mock_process = mock.Mock(spec=ElectricalSignatureProcess)
    mock_process.__str__ = mock.Mock(return_value="Process")
    mock_start_processes.return_value = [mock_process]

    out = StringIO()
    call_command("send_electrical_signature_processes", stdout=out)

    assert mock_start_processes.call_count == 1
    assert mock_start_processes.call_args_list[0][0][0] == non_exempt_plan

    exempt_plan.refresh_from_db()
    non_exempt_plan.refresh_from_db()
    assert exempt_plan.risk_advisor_notification_sent is False
    assert non_exempt_plan.risk_advisor_notification_sent is True


@pytest.mark.django_db
@mock.patch(
    "radiation_protection.management.commands.send_electrical_signature_processes.start_electrical_signature_processes"  # pylint: disable=line-too-long
)
def test_send_electrical_signature_processes_command_no_plans(mock_start_processes):
    """Test the command when there are no plans to process."""
    out = StringIO()
    call_command("send_electrical_signature_processes", stdout=out)

    output = out.getvalue()
    assert "Found 0 risk prevention plans to process" in output
    mock_start_processes.assert_not_called()


@pytest.mark.django_db
@mock.patch(
    "radiation_protection.management.commands.send_electrical_signature_processes.start_electrical_signature_processes"  # pylint: disable=line-too-long
)
def test_send_electrical_signature_processes_command_already_sent(mock_start_processes):
    """Test the command skips plans that were already sent."""
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
    mock_start_processes,
):
    """Test the command with multiple plans to process."""
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
