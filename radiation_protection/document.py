import logging
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING

from django.conf import settings
from django.core import mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import strip_tags
from docx import Document
from docx.text.paragraph import Paragraph

from euphro_auth.models import User
from lab.runs.models import Run
from radiation_protection.models import RiskPreventionPlan

if TYPE_CHECKING:
    from docx.document import Document as DocumentObject


logger = logging.getLogger(__name__)


def _get_document_paths() -> list[Path]:
    """Get the path to the radiation protection template document."""
    base_path = Path(settings.BASE_DIR) / "radiation_protection" / "assets"
    return [
        base_path / "AGLAE_plan_de_prevention_fr.docx",
        base_path / "AGLAE_plan_de_prevention_en.docx",
    ]


def replace_text_in_paragraph(paragraph: Paragraph, key: str, value: str) -> None:
    """Replace text in a paragraph, even if the key is split across runs,
    preserving formatting.
    """
    # Join all run texts to find the full key
    full_text = "".join(run.text for run in paragraph.runs)
    if key not in full_text:
        return

    # Replace the key with the value in the full text
    new_text = full_text.replace(key, value)

    # Remove all runs except the first
    for _ in range(len(paragraph.runs) - 1):
        paragraph.runs[-1].clear()  # Remove text and formatting
        paragraph._element.remove(  # pylint: disable=protected-access
            paragraph.runs[-1]._element  # pylint: disable=protected-access
        )

    # Set the text of the first run to the new text
    paragraph.runs[0].text = new_text


def _prepare_variables(user: User, next_user_run: Run | None) -> dict[str, str]:
    """Prepare variables for document template replacement."""
    variables: dict[str, str] = {
        "certification_date": timezone.now().strftime("%d/%m/%Y"),
        "user_name": user.get_full_name(),
        "admin_name": "",
        "run_date_start": "",
        "run_date_end": "",
    }

    if next_user_run:
        admin = next_user_run.project.admin
        if admin:
            variables["admin_name"] = admin.get_full_name()

        if next_user_run.start_date:
            variables["run_date_start"] = next_user_run.start_date.strftime("%d/%m/%Y")

        if next_user_run.end_date:
            variables["run_date_end"] = next_user_run.end_date.strftime("%d/%m/%Y")

    return variables


def _replace_variables_in_document(
    doc: "DocumentObject", variables: dict[str, str]
) -> None:
    """Replace variables in document paragraphs and tables."""
    # Replace variables in paragraphs
    for paragraph in doc.paragraphs:
        for key, value in variables.items():
            replace_text_in_paragraph(paragraph, key, value)

    # Replace variables in tables
    for table in doc.tables:
        for col in table.columns:
            for cell in col.cells:
                for paragraph in cell.paragraphs:
                    for key, value in variables.items():
                        replace_text_in_paragraph(paragraph, key, value)


def fill_radiation_protection_documents(
    user: User, next_user_run: Run | None
) -> list[tuple[str, bytes | None]]:
    """Fill the radiation protection document template with user information."""
    documents = []
    for document_path in _get_document_paths():
        documents.append(
            (
                document_path.name,
                _fill_radiation_protection_document(
                    document_path=document_path,
                    user=user,
                    next_user_run=next_user_run,
                ),
            )
        )
    return documents


def _fill_radiation_protection_document(
    document_path: Path,
    user: User,
    next_user_run: Run | None,
) -> bytes | None:
    """
    Fill the radiation protection document template with user information.
    Returns the document content as bytes if successful, None otherwise.
    """

    # Create a copy of the template
    doc = Document(str(document_path))

    # Prepare variables for replacement
    variables = _prepare_variables(user, next_user_run)

    # Replace variables in document
    _replace_variables_in_document(doc, variables)

    # Save the document to a bytes buffer
    buffer = BytesIO()
    doc.save(buffer)
    return buffer.getvalue()


def send_document_to_risk_advisor(
    plan: RiskPreventionPlan, documents: list[tuple[str, bytes]]
) -> bool:
    """
    Send the filled radiation protection document to the risk advisor.
    Returns True if the email was sent successfully, False otherwise.
    """
    risk_advisor_emails = settings.RADIATION_PROTECTION_RISK_ADVISOR_EMAILS

    context = {
        "plan": plan,
    }

    user_full_name = plan.participation.user.get_full_name()
    subject = f"Document de certification des risques AGLAE pour {user_full_name}"

    html_message = render_to_string(
        "radiation_protection/email/document_notification.html", context
    )
    plain_message = strip_tags(html_message)

    sending_statuses = []

    for risk_advisor_email in risk_advisor_emails:
        try:
            email = mail.EmailMultiAlternatives(
                subject=subject,
                body=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[risk_advisor_email],
                attachments=[
                    (
                        f"{user_full_name}_{document_name}",
                        document,
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # pylint: disable=line-too-long
                    )
                    for document_name, document in documents
                ],
            )
            email.attach_alternative(html_message, "text/html")
            email.send()
            sending_statuses.append(True)
        except Exception as e:
            logger.error(
                "Failed to send radiation protection document to risk advisor "
                "for user %s: %s",
                plan.participation.user.id,
                str(e),
            )
            sending_statuses.append(False)

    return all(sending_statuses)
