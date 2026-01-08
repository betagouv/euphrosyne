import tempfile
from pathlib import Path

from django.conf import settings
from django.utils import translation

from radiation_protection.app_settings import settings as app_settings
from radiation_protection.document import (
    write_authorization_access_form,
    write_risk_prevention_plan,
)
from radiation_protection.models import ElectricalSignatureProcess, RiskPreventionPlan

from .providers.goodflag import StepType, start_workflow

ELECTRICAL_SIGNATURE_PROVIDER_NAME = "goodflag"


def start_electrical_signature_processes(  # pylint: disable=too-many-locals
    risk_prevention_plan: RiskPreventionPlan,
) -> list[ElectricalSignatureProcess]:
    """
    Function to start an electrical signature process for a given risk prevention plan.
    This function interacts with the external electrical signature service
    provider's API to initiate the process and create an ElectricalSignatureProcess
    instance.

    Args:
        risk_prevention_plan (RiskPreventionPlan): The risk prevention
        plan for which to start the process.

    Returns:
        ElectricalSignatureProcess: The created electrical signature process instance.
    """
    # Interact with the external API to start the process
    # For example, you might send a request to the provider's API here
    run = risk_prevention_plan.run
    risk_advisor_email = app_settings.RADIATION_PROTECTION_RISK_ADVISOR_EMAIL  # type: ignore[misc] # pylint: disable=line-too-long
    parts = app_settings.RADIATION_PROTECTION_RISK_ADVISOR_FULLNAME.rsplit(" ", 1)  # type: ignore[misc] # pylint: disable=line-too-long
    risk_advisor_first_name, risk_advisor_last_name = (
        (parts[0], parts[1]) if len(parts) == 2 else (parts[0], "")
    )

    participation = risk_prevention_plan.participation

    processes: list[ElectricalSignatureProcess] = []

    if not risk_advisor_email:
        raise ValueError(
            "RADIATION_PROTECTION_RISK_ADVISOR_EMAIL setting is not configured."
        )

    employer = participation.employer

    if not employer:
        raise ValueError(f"Participation {participation.id} has no employer.")

    institution_locale = (
        participation.institution.get_administrative_locale()
        if participation.institution
        else getattr(settings, "DEFAULT_LOCALE", "fr")
    )
    with translation.override(institution_locale):
        prevention_plan_base_label = translation.gettext("Risk prevention plan")
        access_form_base_label = translation.gettext("Access authorization form")
    run_date_str = run.start_date.strftime("%d/%m/%y") if run.start_date else ""

    # AUTHORIZATION ACCESS FORM
    with tempfile.NamedTemporaryFile(suffix=".docx") as temp_file:
        workflow_name = f"AGLAE - {access_form_base_label} - {participation.user.get_administrative_name()} - {run.project.name} - {run_date_str}"  # pylint: disable=line-too-long
        write_authorization_access_form(
            plan=risk_prevention_plan,
            write_path=Path(temp_file.name),
        )

        workflow_id = start_workflow(
            workflow_name=workflow_name,
            steps=[
                {
                    "step_type": StepType.APPROVAL,
                    "recipients": [
                        {
                            "email": participation.user.email,
                            "first_name": participation.user.first_name,
                            "last_name": participation.user.last_name,
                            "preferred_locale": institution_locale,
                        },
                    ],
                },
                {
                    "step_type": StepType.SIGNATURE,
                    "recipients": [
                        {
                            "email": employer.email,
                            "first_name": employer.first_name,
                            "last_name": employer.last_name,
                            "preferred_locale": institution_locale,
                        },
                    ],
                },
            ],
            document_path=temp_file.name,
        )
        processes.append(
            ElectricalSignatureProcess.objects.create(
                risk_prevention_plan=risk_prevention_plan,
                provider_name="goodflag",
                provider_workflow_id=workflow_id,
                label=workflow_name,
            )
        )

        # RISK PREVENTION PLAN
        with tempfile.NamedTemporaryFile(suffix=".docx") as temp_file:
            workflow_name = f"AGLAE - {prevention_plan_base_label} - {participation.user.get_administrative_name()} - {run.project.name} - {run_date_str}"  # pylint: disable=line-too-long
            write_risk_prevention_plan(
                plan=risk_prevention_plan,
                write_path=Path(temp_file.name),
            )

            workflow_id = start_workflow(
                workflow_name=workflow_name,
                steps=[
                    {
                        "step_type": StepType.APPROVAL,
                        "recipients": [
                            {
                                "email": participation.user.email,
                                "first_name": participation.user.first_name,
                                "last_name": participation.user.last_name,
                                "preferred_locale": institution_locale,
                            },
                        ],
                    },
                    {
                        "step_type": StepType.SIGNATURE,
                        "recipients": [
                            {
                                "email": employer.email,
                                "first_name": employer.first_name,
                                "last_name": employer.last_name,
                                "preferred_locale": institution_locale,
                            },
                        ],
                    },
                    {
                        "step_type": StepType.SIGNATURE,
                        "recipients": [
                            {
                                "email": risk_advisor_email,
                                "first_name": risk_advisor_first_name or "",
                                "last_name": risk_advisor_last_name or "",
                            },
                        ],
                    },
                ],
                document_path=temp_file.name,
            )

        processes.append(
            ElectricalSignatureProcess.objects.create(
                risk_prevention_plan=risk_prevention_plan,
                provider_name="goodflag",
                provider_workflow_id=workflow_id,
                label=workflow_name,
            )
        )
        return processes
