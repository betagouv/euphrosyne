from datetime import timedelta
from pathlib import Path
from typing import TYPE_CHECKING
from unittest import mock

import pytest
from django.core import mail
from django.test import override_settings
from django.utils import timezone
from docx import Document

from certification.certifications.models import QuizResult
from certification.certifications.tests.factories import QuizCertificationFactory
from euphro_auth.tests import factories as auth_factories
from lab.runs.models import Run
from lab.tests import factories as lab_factories
from radiation_protection.certification import get_radioprotection_certification
from radiation_protection.document import (
    _fill_radiation_protection_document,
    _prepare_variables,
    _replace_variables_in_document,
    fill_radiation_protection_documents,
    replace_text_in_paragraph,
    send_document_to_risk_advisor,
)
from radiation_protection.models import RiskPreventionPlan

if TYPE_CHECKING:
    from docx.document import Document as DocumentObject


@pytest.fixture(name="mock_document_paths")
def mock_document_paths_fixture(settings):
    """Create mock document paths for testing."""
    base_path = Path(settings.BASE_DIR) / "radiation_protection" / "assets"
    return [
        base_path / "AGLAE_plan_de_prevention_fr.docx",
        base_path / "AGLAE_plan_de_prevention_en.docx",
    ]


@pytest.fixture(name="mock_document")
def mock_document_fixture():
    """Create a mock document with test content."""
    doc = Document()
    doc.add_paragraph("Test document for user_name")
    doc.add_paragraph("Admin: admin_name")
    doc.add_paragraph("Start: run_date_start")
    doc.add_paragraph("End: run_date_end")
    doc.add_paragraph("Certification date: certification_date")
    return doc


@pytest.fixture(name="quiz_result")
def quiz_result_fixture():
    """Create a quiz result for testing."""
    user = auth_factories.StaffUserFactory()
    quiz = QuizCertificationFactory(certification=get_radioprotection_certification())
    return QuizResult.objects.create(
        user=user,
        quiz=quiz,
        is_passed=True,
        score=95,
    )


@pytest.fixture(name="next_user_run")
def next_user_run_fixture():
    """Create a next user run for testing."""
    admin = auth_factories.StaffUserFactory()
    project = lab_factories.ProjectFactory(admin=admin)
    return lab_factories.RunFactory(
        project=project,
        start_date=timezone.now() + timedelta(days=7),
        end_date=timezone.now() + timedelta(days=14),
    )


def test_replace_text_in_paragraph():
    """Test text replacement in a paragraph."""
    doc = Document()
    paragraph = doc.add_paragraph("Hello ${name}!")
    replace_text_in_paragraph(paragraph, "${name}", "John")
    assert paragraph.text == "Hello John!"


@pytest.mark.django_db
def test_prepare_variables_with_run(quiz_result: QuizResult, next_user_run: Run):
    """Test preparing variables when run is available."""
    variables = _prepare_variables(quiz_result.user, next_user_run)

    assert variables["user_name"] == quiz_result.user.get_full_name()  # type: ignore # pylint: disable=line-too-long
    assert variables["admin_name"] == next_user_run.project.admin.get_full_name()  # type: ignore # pylint: disable=line-too-long
    assert variables["run_date_start"] == next_user_run.start_date.strftime(  # type: ignore # pylint: disable=line-too-long
        "%d/%m/%Y"
    )
    assert variables["run_date_end"] == next_user_run.end_date.strftime(  # type: ignore # pylint: disable=line-too-long
        "%d/%m/%Y"
    )
    assert variables["certification_date"] == quiz_result.created.strftime("%d/%m/%Y")


@pytest.mark.django_db
def test_prepare_variables_without_run(quiz_result: QuizResult):
    """Test preparing variables when no run is available."""
    variables = _prepare_variables(quiz_result.user, None)

    assert variables["user_name"] == quiz_result.user.get_full_name()  # type: ignore
    assert variables["admin_name"] == ""
    assert variables["run_date_start"] == ""
    assert variables["run_date_end"] == ""
    assert variables["certification_date"] == quiz_result.created.strftime("%d/%m/%Y")


@pytest.mark.django_db
def test_prepare_variables_without_passed_quiz_result(quiz_result: QuizResult):
    """Test preparing variables when no run is available."""
    with mock.patch(
        "radiation_protection.document.get_user_passed_certification_date"
    ) as mock_date:
        mock_date.return_value = None
        variables = _prepare_variables(quiz_result.user, None)

    assert variables["user_name"] == quiz_result.user.get_full_name()  # type: ignore
    assert variables["admin_name"] == ""
    assert variables["run_date_start"] == ""
    assert variables["run_date_end"] == ""
    assert variables["certification_date"] == ""


def test_replace_variables_in_document(mock_document: "DocumentObject"):
    """Test replacing variables in document."""
    variables = {
        "user_name": "John Doe",
        "admin_name": "Admin User",
        "run_date_start": "01/01/2024",
        "run_date_end": "02/01/2024",
        "certification_date": "03/01/2024",
    }

    _replace_variables_in_document(mock_document, variables)

    assert mock_document.paragraphs[0].text == "Test document for John Doe"
    assert mock_document.paragraphs[1].text == "Admin: Admin User"
    assert mock_document.paragraphs[2].text == "Start: 01/01/2024"
    assert mock_document.paragraphs[3].text == "End: 02/01/2024"
    assert mock_document.paragraphs[4].text == "Certification date: 03/01/2024"


@pytest.mark.django_db
@mock.patch("radiation_protection.document.Document")
def test_fill_radiation_protection_document(
    mock_document_class,
    mock_document: "DocumentObject",
    quiz_result: QuizResult,
    next_user_run: Run,
    mock_document_paths: list[Path],
):
    """Test filling the radiation protection document."""
    mock_document_class.return_value = mock_document
    mock_document_paths[0].parent.mkdir(parents=True, exist_ok=True)
    mock_document_paths[0].touch()

    result = _fill_radiation_protection_document(
        document_path=mock_document_paths[0],
        user=quiz_result.user,
        next_user_run=next_user_run,
    )

    assert result is not None
    assert isinstance(result, bytes)


@pytest.mark.django_db
def test_fill_radiation_protection_documents(
    quiz_result: QuizResult,
    next_user_run: Run,
):
    """Test filling multiple radiation protection documents."""
    with mock.patch(
        "radiation_protection.document._fill_radiation_protection_document"
    ) as mock_fill:
        mock_fill.return_value = b"test content"
        documents = fill_radiation_protection_documents(
            user=quiz_result.user, next_user_run=next_user_run
        )

        assert len(documents) == 2
        assert all(isinstance(doc[1], bytes) for doc in documents)
        assert mock_fill.call_count == 2


@override_settings(
    RADIATION_PROTECTION_RISK_ADVISOR_EMAILS=[
        "risk@example.com",
        "another_risk@example.com",
    ],
    DEFAULT_FROM_EMAIL="noreply@example.com",
)
@pytest.mark.django_db
def test_send_document_to_risk_advisors():
    """Test sending document to risk advisors."""
    user = auth_factories.StaffUserFactory()
    participation = lab_factories.ParticipationFactory(user=user)
    run = lab_factories.RunFactory(
        start_date=timezone.now() + timedelta(days=7),
    )
    plan = RiskPreventionPlan.objects.create(
        participation=participation,
        run=run,
    )

    documents = [
        ("test_fr.docx", b"French content"),
        ("test_en.docx", b"English content"),
    ]

    result = send_document_to_risk_advisor(plan, documents)

    assert result is True
    assert len(mail.outbox) == 2
    email1 = mail.outbox[0]
    email2 = mail.outbox[1]
    assert email1.to == ["risk@example.com"]
    assert email2.to == ["another_risk@example.com"]
    assert (
        email1.subject
        == f"Document de certification des risques AGLAE pour {user.get_full_name()}"
    )
    assert (
        email2.subject
        == f"Document de certification des risques AGLAE pour {user.get_full_name()}"
    )
    assert len(email1.attachments) == 2
    assert len(email2.attachments) == 2
