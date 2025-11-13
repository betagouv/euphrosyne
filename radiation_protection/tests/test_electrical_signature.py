from unittest import mock

import pytest

from lab.tests import factories as lab_factories
from radiation_protection.electrical_signature.electrical_signature import (
    start_electrical_signature_processes,
)
from radiation_protection.models import ElectricalSignatureProcess
from radiation_protection.tests import factories as radiation_factories


@pytest.fixture(name="risk_prevention_plan")
def risk_prevention_plan_fixture():
    """Create a risk prevention plan with all required relationships."""
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
        participation=participation, run=run
    )


@pytest.mark.django_db
@mock.patch(
    "radiation_protection.electrical_signature.electrical_signature.start_workflow"
)
def test_start_electrical_signature_processes(
    mock_start_workflow, risk_prevention_plan, settings
):
    """Test starting electrical signature processes."""
    settings.RADIATION_PROTECTION_RISK_ADVISOR_EMAIL = "advisor@example.com"
    settings.RADIATION_PROTECTION_RISK_ADVISOR_FULLNAME = "John Advisor"

    mock_start_workflow.side_effect = ["workflow_auth_123", "workflow_risk_123"]

    processes = start_electrical_signature_processes(risk_prevention_plan)

    # Verify two processes are created
    assert len(processes) == 2

    # Verify the processes were saved to the database
    assert ElectricalSignatureProcess.objects.count() == 2

    # Check authorization access form process
    auth_process = processes[0]
    assert auth_process.provider_name == "goodflag"
    assert auth_process.provider_workflow_id == "workflow_auth_123"
    assert "Formulaire d'autorisation d'accès" in auth_process.label
    assert not auth_process.is_completed
    assert auth_process.risk_prevention_plan == risk_prevention_plan

    # Check risk prevention plan process
    risk_process = processes[1]
    assert risk_process.provider_name == "goodflag"
    assert risk_process.provider_workflow_id == "workflow_risk_123"
    assert "Plan de prévention des risques" in risk_process.label
    assert not risk_process.is_completed
    assert risk_process.risk_prevention_plan == risk_prevention_plan

    # Verify start_workflow was called twice
    assert mock_start_workflow.call_count == 2


@pytest.mark.django_db
@mock.patch(
    "radiation_protection.electrical_signature.electrical_signature.start_workflow"
)
def test_start_electrical_signature_processes_workflow_steps(
    mock_start_workflow, risk_prevention_plan, settings
):
    """Test that the correct workflow steps are created."""
    settings.RADIATION_PROTECTION_RISK_ADVISOR_EMAIL = "advisor@example.com"
    settings.RADIATION_PROTECTION_RISK_ADVISOR_FULLNAME = "John Advisor"

    mock_start_workflow.side_effect = ["workflow_auth_123", "workflow_risk_123"]

    start_electrical_signature_processes(risk_prevention_plan)

    # Verify the calls to start_workflow
    assert mock_start_workflow.call_count == 2

    # Check authorization access form workflow
    auth_call = mock_start_workflow.call_args_list[0]
    auth_steps = auth_call[1]["steps"]
    assert len(auth_steps) == 2  # Approval + Signature
    assert auth_steps[0]["step_type"].value == "approval"
    assert auth_steps[1]["step_type"].value == "signature"

    # Verify recipients for auth form
    assert (
        auth_steps[0]["recipients"][0]["email"]
        == risk_prevention_plan.participation.user.email
    )
    assert (
        auth_steps[1]["recipients"][0]["email"]
        == risk_prevention_plan.participation.employer.email
    )

    # Check risk prevention plan workflow
    risk_call = mock_start_workflow.call_args_list[1]
    risk_steps = risk_call[1]["steps"]
    assert len(risk_steps) == 3  # Approval + 2 Signatures
    assert risk_steps[0]["step_type"].value == "approval"
    assert risk_steps[1]["step_type"].value == "signature"
    assert risk_steps[2]["step_type"].value == "signature"

    # Verify recipients for risk prevention plan
    assert (
        risk_steps[0]["recipients"][0]["email"]
        == risk_prevention_plan.participation.user.email
    )
    assert (
        risk_steps[1]["recipients"][0]["email"]
        == risk_prevention_plan.participation.employer.email
    )
    assert risk_steps[2]["recipients"][0]["email"] == "advisor@example.com"


@pytest.mark.django_db
@mock.patch(
    "radiation_protection.electrical_signature.electrical_signature.start_workflow"
)
def test_start_electrical_signature_processes_workflow_names(
    mock_start_workflow, risk_prevention_plan, settings
):
    """Test that workflow names include user, project, and run information."""
    settings.RADIATION_PROTECTION_RISK_ADVISOR_EMAIL = "advisor@example.com"
    settings.RADIATION_PROTECTION_RISK_ADVISOR_FULLNAME = "John Advisor"

    mock_start_workflow.side_effect = ["workflow_auth_123", "workflow_risk_123"]

    start_electrical_signature_processes(risk_prevention_plan)

    # Check authorization access form workflow name
    auth_call = mock_start_workflow.call_args_list[0]
    auth_workflow_name = auth_call[1]["workflow_name"]
    assert "Formulaire d'autorisation d'accès" in auth_workflow_name
    assert (
        risk_prevention_plan.participation.user.get_administrative_name()
        in auth_workflow_name
    )
    assert risk_prevention_plan.run.project.name in auth_workflow_name
    assert risk_prevention_plan.run.label in auth_workflow_name

    # Check risk prevention plan workflow name
    risk_call = mock_start_workflow.call_args_list[1]
    risk_workflow_name = risk_call[1]["workflow_name"]
    assert "Plan de prévention des risques" in risk_workflow_name
    assert (
        risk_prevention_plan.participation.user.get_administrative_name()
        in risk_workflow_name
    )
    assert risk_prevention_plan.run.project.name in risk_workflow_name
    assert risk_prevention_plan.run.label in risk_workflow_name
