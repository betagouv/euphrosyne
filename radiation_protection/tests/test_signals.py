from datetime import timedelta
from unittest import mock

import pytest
from django.test import override_settings
from django.utils import timezone

from certification.certifications.models import QuizResult
from certification.certifications.tests.factories import (
    QuizCertificationFactory,
    QuizResultFactory,
)
from euphro_auth.tests import factories as auth_factories
from lab.participations.models import Participation
from lab.runs.models import Run
from lab.tests import factories as lab_factories
from radiation_protection.signals import handle_radiation_protection_certification


@pytest.fixture(name="quiz_result")
def quiz_result_fixture():
    """Create a quiz result for testing."""
    user = auth_factories.StaffUserFactory()
    quiz = QuizCertificationFactory(certification__name="radiation_protection")
    return QuizResult.objects.create(
        user=user,
        quiz=quiz,
        is_passed=True,
        score=95,
    )


@pytest.fixture(name="next_user_run")
def next_user_run_fixture(quiz_result: QuizResult):
    """Create a next user run for testing."""
    admin = auth_factories.StaffUserFactory()
    project = lab_factories.ProjectFactory(admin=admin)
    run = lab_factories.RunFactory(
        project=project,
        start_date=timezone.now() + timedelta(days=7),
        end_date=timezone.now() + timedelta(days=14),
    )
    Participation.objects.create(user=quiz_result.user, project=project)
    return run


@pytest.mark.django_db
@override_settings(RADIATION_PROTECTION_CERTIFICATION_NAME="radiation_protection")
def test_handle_radiation_protection_certification(
    quiz_result: QuizResult, next_user_run: Run
):
    """Test the signal handler for radiation protection certification."""
    # Ensure quiz_result is passed
    quiz_result.is_passed = True
    quiz_result.save()

    # Mock the functions
    with mock.patch(
        "radiation_protection.signals.fill_radiation_protection_documents"
    ) as mock_fill, mock.patch(
        "radiation_protection.signals.send_document_to_risk_advisor"
    ) as mock_send:
        mock_fill.return_value = [("test.docx", b"content")]
        mock_send.return_value = True

        # Call the handler directly
        handle_radiation_protection_certification(
            sender=QuizResult,
            instance=quiz_result,
            created=True,
        )

        # Verify that the mocked functions were called
        mock_fill.assert_called_once_with(
            quiz_result=quiz_result,
            next_user_run=next_user_run,
        )
        mock_send.assert_called_once()


@pytest.mark.django_db
@override_settings(RADIATION_PROTECTION_CERTIFICATION_NAME="radiation_protection")
def test_handle_radiation_protection_certification_not_passed(
    quiz_result: QuizResult,
):
    """Test signal handler when quiz is not passed."""
    quiz_result.is_passed = False
    quiz_result.save()

    # Mock the functions
    with mock.patch(
        "radiation_protection.document.fill_radiation_protection_documents"
    ) as mock_fill, mock.patch(
        "radiation_protection.document.send_document_to_risk_advisor"
    ) as mock_send:
        # Call the handler directly
        handle_radiation_protection_certification(
            sender=QuizResult,
            instance=quiz_result,
            created=True,
        )

        # Verify that the mocked functions were not called
        mock_fill.assert_not_called()
        mock_send.assert_not_called()


@pytest.mark.django_db
@override_settings(RADIATION_PROTECTION_CERTIFICATION_NAME="radiation_protection")
def test_handle_radiation_protection_certification_not_created(
    quiz_result: QuizResult,
):
    """Test signal handler when quiz result is not newly created."""
    # Mock the functions
    with mock.patch(
        "radiation_protection.document.fill_radiation_protection_documents"
    ) as mock_fill, mock.patch(
        "radiation_protection.document.send_document_to_risk_advisor"
    ) as mock_send:
        # Call the handler directly
        handle_radiation_protection_certification(
            sender=QuizResult,
            instance=quiz_result,
            created=False,
        )

        # Verify that the mocked functions were not called
        mock_fill.assert_not_called()
        mock_send.assert_not_called()


@pytest.mark.django_db
@override_settings(RADIATION_PROTECTION_CERTIFICATION_NAME="radiation_protection")
@mock.patch("radiation_protection.signals.send_document_to_risk_advisor")
def test_signal_is_sent(mock_send_document_to_risk_advisor: mock.Mock):
    """Test that the signal is sent when the quiz is passed."""
    QuizResultFactory(
        quiz__certification__name="radiation_protection",
        is_passed=True,
        score=95,
    )
    mock_send_document_to_risk_advisor.assert_called_once()
