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
    "radiation_protection.electrical_signature.electrical_signature.start_workflow"
)
def test_start_electrical_signature_processes(
    mock_start_workflow, risk_prevention_plan
):
    """Test starting electrical signature processes."""
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
    assert "AGLAE - " in auth_process.label
    assert not auth_process.is_completed
    assert auth_process.risk_prevention_plan == risk_prevention_plan

    # Check risk prevention plan process
    risk_process = processes[1]
    assert risk_process.provider_name == "goodflag"
    assert risk_process.provider_workflow_id == "workflow_risk_123"
    assert "AGLAE - " in risk_process.label
    assert not risk_process.is_completed
    assert risk_process.risk_prevention_plan == risk_prevention_plan

    # Verify start_workflow was called twice
    assert mock_start_workflow.call_count == 2


@pytest.mark.django_db
@mock.patch(
    "radiation_protection.electrical_signature.electrical_signature.start_workflow"
)
def test_start_electrical_signature_processes_workflow_steps(
    mock_start_workflow, risk_prevention_plan
):
    """Test that the correct workflow steps are created."""
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
    mock_start_workflow, risk_prevention_plan
):
    """Test that workflow names include AGLAE prefix, user, project,
    and run information."""
    mock_start_workflow.side_effect = ["workflow_auth_123", "workflow_risk_123"]

    start_electrical_signature_processes(risk_prevention_plan)

    # Check authorization access form workflow name
    auth_call = mock_start_workflow.call_args_list[0]
    auth_workflow_name = auth_call[1]["workflow_name"]
    assert auth_workflow_name.startswith("AGLAE - ")
    assert (
        risk_prevention_plan.participation.user.get_administrative_name()
        in auth_workflow_name
    )
    assert risk_prevention_plan.run.project.name in auth_workflow_name

    # Check risk prevention plan workflow name
    risk_call = mock_start_workflow.call_args_list[1]
    risk_workflow_name = risk_call[1]["workflow_name"]
    assert risk_workflow_name.startswith("AGLAE - ")
    assert (
        risk_prevention_plan.participation.user.get_administrative_name()
        in risk_workflow_name
    )
    assert risk_prevention_plan.run.project.name in risk_workflow_name


@pytest.mark.django_db
@mock.patch(
    "radiation_protection.electrical_signature.electrical_signature.start_workflow"
)
@mock.patch(
    "radiation_protection.electrical_signature.electrical_signature.translation"
)
def test_start_electrical_signature_processes_english_translation(
    mock_translation, mock_start_workflow
):
    """Test that translation.override is called with 'en'
    for non-French institutions."""
    # Create a risk prevention plan with a non-French institution
    user = lab_factories.StaffUserFactory()
    admin = lab_factories.StaffUserFactory()
    project = lab_factories.ProjectFactory(admin=admin)
    run = lab_factories.RunFactory(project=project)
    institution = lab_factories.InstitutionFactory(country="United States")
    employer = lab_factories.EmployerFactory()

    participation = project.participation_set.create(
        user=user, institution=institution, employer=employer
    )

    risk_prevention_plan = radiation_factories.RiskPreventionPlanFactory(
        participation=participation, run=run
    )

    mock_start_workflow.side_effect = ["workflow_auth_123", "workflow_risk_123"]

    start_electrical_signature_processes(risk_prevention_plan)

    # Verify that translation.override was called with 'en' for US institution
    mock_translation.override.assert_called_once_with("en")


@pytest.mark.django_db
@mock.patch(
    "radiation_protection.electrical_signature.electrical_signature.start_workflow"
)
@mock.patch(
    "radiation_protection.electrical_signature.electrical_signature.translation"
)
def test_start_electrical_signature_processes_french_institution(
    mock_translation, mock_start_workflow
):
    """Test that translation.override is called with 'fr' for French institutions."""
    # Create a risk prevention plan with a French institution
    user = lab_factories.StaffUserFactory()
    admin = lab_factories.StaffUserFactory()
    project = lab_factories.ProjectFactory(admin=admin)
    run = lab_factories.RunFactory(project=project)
    institution = lab_factories.InstitutionFactory(country="France")
    employer = lab_factories.EmployerFactory()

    participation = project.participation_set.create(
        user=user, institution=institution, employer=employer
    )

    risk_prevention_plan = radiation_factories.RiskPreventionPlanFactory(
        participation=participation, run=run
    )

    mock_start_workflow.side_effect = ["workflow_auth_123", "workflow_risk_123"]

    start_electrical_signature_processes(risk_prevention_plan)

    # Verify that translation.override was called with 'fr' for French institution
    mock_translation.override.assert_called_once_with("fr")


@pytest.mark.django_db
@mock.patch(
    "radiation_protection.electrical_signature.electrical_signature.start_workflow"
)
@mock.patch(
    "radiation_protection.electrical_signature.electrical_signature.translation"
)
def test_start_electrical_signature_processes_no_institution(
    mock_translation, mock_start_workflow
):
    """Test that translation.override defaults to 'fr'
    when no institution is provided."""
    # Create a risk prevention plan without institution
    user = lab_factories.StaffUserFactory()
    admin = lab_factories.StaffUserFactory()
    project = lab_factories.ProjectFactory(admin=admin)
    run = lab_factories.RunFactory(project=project)
    employer = lab_factories.EmployerFactory()

    participation = project.participation_set.create(
        user=user, institution=None, employer=employer
    )

    risk_prevention_plan = radiation_factories.RiskPreventionPlanFactory(
        participation=participation, run=run
    )

    mock_start_workflow.side_effect = ["workflow_auth_123", "workflow_risk_123"]

    start_electrical_signature_processes(risk_prevention_plan)

    # Verify that translation.override was called with default locale 'fr'
    mock_translation.override.assert_called_once_with("fr")


@pytest.mark.django_db
@mock.patch(
    "radiation_protection.electrical_signature.electrical_signature.start_workflow"
)
def test_start_electrical_signature_processes_uses_run_date(mock_start_workflow):
    """Test that workflow names include formatted run start date."""
    user = lab_factories.StaffUserFactory()
    admin = lab_factories.StaffUserFactory()
    project = lab_factories.ProjectFactory(admin=admin)
    run = lab_factories.RunFactory(project=project)
    institution = lab_factories.InstitutionFactory()
    employer = lab_factories.EmployerFactory()

    participation = project.participation_set.create(
        user=user, institution=institution, employer=employer
    )

    risk_prevention_plan = radiation_factories.RiskPreventionPlanFactory(
        participation=participation, run=run
    )

    mock_start_workflow.side_effect = ["workflow_auth_123", "workflow_risk_123"]

    start_electrical_signature_processes(risk_prevention_plan)

    # Check that both workflow names include the run start date
    auth_call = mock_start_workflow.call_args_list[0]
    auth_workflow_name = auth_call[1]["workflow_name"]
    run_date_str = run.start_date.strftime("%d/%m/%y")
    assert run_date_str in auth_workflow_name

    risk_call = mock_start_workflow.call_args_list[1]
    risk_workflow_name = risk_call[1]["workflow_name"]
    assert run_date_str in risk_workflow_name


@pytest.mark.django_db
@mock.patch(
    "radiation_protection.electrical_signature.electrical_signature.start_workflow"
)
def test_start_electrical_signature_processes_preferred_locale_for_french(  # pylint: disable=too-many-locals
    mock_start_workflow,
):
    """Test that preferred_locale is set to 'fr' for French institutions."""
    user = lab_factories.StaffUserFactory()
    admin = lab_factories.StaffUserFactory()
    project = lab_factories.ProjectFactory(admin=admin)
    run = lab_factories.RunFactory(project=project)
    institution = lab_factories.InstitutionFactory(country="France")
    employer = lab_factories.EmployerFactory()

    participation = project.participation_set.create(
        user=user, institution=institution, employer=employer
    )

    risk_prevention_plan = radiation_factories.RiskPreventionPlanFactory(
        participation=participation, run=run
    )

    mock_start_workflow.side_effect = ["workflow_auth_123", "workflow_risk_123"]

    start_electrical_signature_processes(risk_prevention_plan)

    # Check authorization access form - verify preferred_locale for user and employer
    auth_call = mock_start_workflow.call_args_list[0]
    auth_steps = auth_call[1]["steps"]
    for step in auth_steps:
        for recipient in step["recipients"]:
            assert recipient["preferred_locale"] == "fr"

    # Check risk prevention plan - verify preferred_locale for user and employer
    # Note: advisor (third step) doesn't have preferred_locale set
    risk_call = mock_start_workflow.call_args_list[1]
    risk_steps = risk_call[1]["steps"]
    # Check first two steps (approval and employer signature)
    for step in risk_steps[:2]:
        for recipient in step["recipients"]:
            assert recipient["preferred_locale"] == "fr"


@pytest.mark.django_db
@mock.patch(
    "radiation_protection.electrical_signature.electrical_signature.start_workflow"
)
def test_start_electrical_signature_processes_preferred_locale_for_english(  # pylint: disable=too-many-locals
    mock_start_workflow,
):
    """Test that preferred_locale is set to 'en' for non-French institutions."""
    user = lab_factories.StaffUserFactory()
    admin = lab_factories.StaffUserFactory()
    project = lab_factories.ProjectFactory(admin=admin)
    run = lab_factories.RunFactory(project=project)
    institution = lab_factories.InstitutionFactory(country="United States")
    employer = lab_factories.EmployerFactory()

    participation = project.participation_set.create(
        user=user, institution=institution, employer=employer
    )

    risk_prevention_plan = radiation_factories.RiskPreventionPlanFactory(
        participation=participation, run=run
    )

    mock_start_workflow.side_effect = ["workflow_auth_123", "workflow_risk_123"]

    start_electrical_signature_processes(risk_prevention_plan)

    # Check authorization access form - verify preferred_locale for user and employer
    auth_call = mock_start_workflow.call_args_list[0]
    auth_steps = auth_call[1]["steps"]
    for step in auth_steps:
        for recipient in step["recipients"]:
            assert recipient["preferred_locale"] == "en"

    # Check risk prevention plan - verify preferred_locale for user and employer
    # Note: advisor (third step) doesn't have preferred_locale set
    risk_call = mock_start_workflow.call_args_list[1]
    risk_steps = risk_call[1]["steps"]
    # Check first two steps (approval and employer signature)
    for step in risk_steps[:2]:
        for recipient in step["recipients"]:
            assert recipient["preferred_locale"] == "en"


@pytest.mark.django_db
@mock.patch(
    "radiation_protection.electrical_signature.electrical_signature.start_workflow"
)
def test_risk_advisor_name_with_middle_name(
    mock_start_workflow, risk_prevention_plan
):
    """Test that names with middle names are handled correctly using rsplit."""
    with (
        mock.patch(
            "radiation_protection.electrical_signature.electrical_signature."
            "app_settings.RADIATION_PROTECTION_RISK_ADVISOR_EMAIL",
            "advisor@example.com",
        ),
        mock.patch(
            "radiation_protection.electrical_signature.electrical_signature."
            "app_settings.RADIATION_PROTECTION_RISK_ADVISOR_FULLNAME",
            "Jean Marie Dupont",
        ),
    ):
        mock_start_workflow.side_effect = ["workflow_auth_123", "workflow_risk_123"]

        start_electrical_signature_processes(risk_prevention_plan)

        # Check risk prevention plan workflow (second call)
        risk_call = mock_start_workflow.call_args_list[1]
        risk_steps = risk_call[1]["steps"]

        # Check advisor (third step) has correct name split
        advisor_recipient = risk_steps[2]["recipients"][0]
        assert advisor_recipient["first_name"] == "Jean Marie"
        assert advisor_recipient["last_name"] == "Dupont"


@pytest.mark.django_db
@mock.patch(
    "radiation_protection.electrical_signature.electrical_signature.start_workflow"
)
def test_risk_advisor_name_with_single_name(
    mock_start_workflow, risk_prevention_plan
):
    """Test that single names are handled correctly."""
    with (
        mock.patch(
            "radiation_protection.electrical_signature.electrical_signature."
            "app_settings.RADIATION_PROTECTION_RISK_ADVISOR_EMAIL",
            "advisor@example.com",
        ),
        mock.patch(
            "radiation_protection.electrical_signature.electrical_signature."
            "app_settings.RADIATION_PROTECTION_RISK_ADVISOR_FULLNAME",
            "Madonna",
        ),
    ):
        mock_start_workflow.side_effect = ["workflow_auth_123", "workflow_risk_123"]

        start_electrical_signature_processes(risk_prevention_plan)

        # Check risk prevention plan workflow (second call)
        risk_call = mock_start_workflow.call_args_list[1]
        risk_steps = risk_call[1]["steps"]

        # Check advisor (third step) has correct name split
        advisor_recipient = risk_steps[2]["recipients"][0]
        assert advisor_recipient["first_name"] == "Madonna"
        assert advisor_recipient["last_name"] == ""


@pytest.mark.django_db
@mock.patch(
    "radiation_protection.electrical_signature.electrical_signature.start_workflow"
)
def test_risk_advisor_name_with_compound_last_name(
    mock_start_workflow, risk_prevention_plan
):
    """Test that compound last names are handled correctly using rsplit."""
    with (
        mock.patch(
            "radiation_protection.electrical_signature.electrical_signature."
            "app_settings.RADIATION_PROTECTION_RISK_ADVISOR_EMAIL",
            "advisor@example.com",
        ),
        mock.patch(
            "radiation_protection.electrical_signature.electrical_signature."
            "app_settings.RADIATION_PROTECTION_RISK_ADVISOR_FULLNAME",
            "John Smith-Johnson",
        ),
    ):
        mock_start_workflow.side_effect = ["workflow_auth_123", "workflow_risk_123"]

        start_electrical_signature_processes(risk_prevention_plan)

        # Check risk prevention plan workflow (second call)
        risk_call = mock_start_workflow.call_args_list[1]
        risk_steps = risk_call[1]["steps"]

        # Check advisor (third step) has correct name split
        advisor_recipient = risk_steps[2]["recipients"][0]
        assert advisor_recipient["first_name"] == "John"
        assert advisor_recipient["last_name"] == "Smith-Johnson"
