import tempfile
from pathlib import Path

from django.conf import settings

from radiation_protection.document import (
    write_authorization_access_form,
    write_risk_prevention_plan,
)
from radiation_protection.models import ElectricalSignatureProcess, RiskPreventionPlan

from .providers.goodflag import StepType, start_workflow

ELECTRICAL_SIGNATURE_PROVIDER_NAME = "goodflag"
RISK_PREVENTION_FILE = "radiation_protection/assets/AGLAE_plan_de_prevention_fr.docx"


def start_electrical_signature_processes(
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
    risk_advisor_email = settings.RADIATION_PROTECTION_RISK_ADVISOR_EMAIL
    risk_advisor_first_name, risk_advisor_last_name = (
        settings.RADIATION_PROTECTION_RISK_ADVISOR_FULLNAME.split(" ", 1)
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

    # AUTHORIZATION ACCESS FORM
    with tempfile.NamedTemporaryFile(suffix=".docx") as temp_file:
        workflow_name = "Formulaire d'autorisation d'accès - %s - %s - %s" % (
            f"{participation.user.get_administrative_name()}",
            run.project.name,
            run.label,
        )
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
            workflow_name = "Plan de prévention des risques - %s - %s - %s" % (
                f"{participation.user.get_administrative_name()}",
                run.project.name,
                run.label,
            )
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
