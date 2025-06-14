import datetime
from unittest import mock

import pytest

from certification.certifications.tests import factories as certification_factories
from certification.models import Certification
from lab.tests import factories

from ..models import CertificationNotification, NotificationType

PATH_TO_COMPLETE = "path/to/complete"
PATH_TO_SUCCESS = "path/to/success"


@pytest.fixture(name="certification")
def certification_fixture():
    certification = certification_factories.CertificationOfTypeQuizFactory(
        name="certification",
        invitation_to_complete_email_template_path=PATH_TO_COMPLETE,
        success_email_template_path=PATH_TO_SUCCESS,
        num_days_valid=365,
    )
    certification_factories.QuizCertificationFactory(
        certification=certification, url="url", passing_score=1
    )
    return certification


@pytest.mark.django_db
@pytest.mark.parametrize(
    "type_of, expected_template",
    [
        (NotificationType.INVITATION_TO_COMPLETE, PATH_TO_COMPLETE),
        (NotificationType.SUCCESS, PATH_TO_SUCCESS),
    ],
)
def test_get_template_for_certification_type(
    type_of: NotificationType, expected_template: str, certification: Certification
):
    notification = CertificationNotification.objects.create(
        type_of=type_of, certification=certification, user=factories.StaffUserFactory()
    )

    assert notification.get_template_for_certification_type() == expected_template


@pytest.mark.django_db
def test_get_context_for_invitation_to_complete(certification: Certification):
    notification = CertificationNotification.objects.create(
        type_of=NotificationType.INVITATION_TO_COMPLETE,
        certification=certification,
        user=factories.StaffUserFactory(),
    )

    with mock.patch(
        # pylint: disable=line-too-long
        "certification.certifications.models.QuizCertificationQuerySet.get_random_next_quizz_for_user"
    ) as mock_fn:
        mock_fn.return_value = certification_factories.QuizCertificationFactory(
            certification=certification, url="url123", passing_score=3232
        )
        context = notification.get_context_for_certification()

        mock_fn.assert_called_once()
        assert context["quiz_link"] == "url123"
        assert context["passing_score"] == 3232
        assert context["user"] == notification.user
        assert context["notification_id"] == notification.id
        assert context["invitation_type"] == str(
            NotificationType.INVITATION_TO_COMPLETE
        )


@pytest.mark.django_db
def test_get_context_for_retry(certification: Certification):
    notification = CertificationNotification.objects.create(
        type_of=NotificationType.RETRY,
        certification=certification,
        user=factories.StaffUserFactory(),
    )

    with mock.patch(
        # pylint: disable=line-too-long
        "certification.certifications.models.QuizCertificationQuerySet.get_random_next_quizz_for_user"
    ) as mock_fn:
        mock_fn.return_value = certification_factories.QuizCertificationFactory(
            certification=certification, url="url123", passing_score=3232
        )
        context = notification.get_context_for_certification()

        mock_fn.assert_called_once()
        assert context["quiz_link"] == "url123"
        assert context["passing_score"] == 3232
        assert context["user"] == notification.user
        assert context["notification_id"] == notification.id
        assert context["invitation_type"] == str(NotificationType.RETRY)


@pytest.mark.django_db
def test_get_context_for_success(certification: Certification):
    user = factories.StaffUserFactory()
    quiz = certification_factories.QuizCertificationFactory(
        certification=certification, url="url", passing_score=1
    )
    result = certification_factories.QuizResultFactory(
        quiz=quiz, user=user, score=1, is_passed=False
    )
    notification = CertificationNotification.objects.create(
        type_of=NotificationType.SUCCESS,
        certification=certification,
        user=user,
        quiz_result=result,
    )

    context = notification.get_context_for_certification()
    assert context
    assert "valid_until" in context
    assert isinstance(context["valid_until"], datetime.datetime)


@pytest.mark.django_db
def test_send_notification_raise_error_if_no_template(certification: Certification):
    with mock.patch.object(
        CertificationNotification,
        "get_template_for_certification_type",
        return_value=None,
    ):
        notification = CertificationNotification.objects.create(
            type_of=NotificationType.INVITATION_TO_COMPLETE,
            certification=certification,
            user=factories.StaffUserFactory(),
        )
        with pytest.raises(ValueError):
            notification.send_notification()


@pytest.mark.django_db
def test_send_notification(certification: Certification):
    with mock.patch("certification.notifications.models.send_notification") as mock_fn:
        notification = CertificationNotification.objects.create(
            type_of=NotificationType.INVITATION_TO_COMPLETE,
            certification=certification,
            user=factories.StaffUserFactory(),
        )
        notification.send_notification()

        assert notification.is_sent
        mock_fn.assert_called_once()
