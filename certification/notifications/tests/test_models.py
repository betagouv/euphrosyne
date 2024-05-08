from unittest import mock

import pytest

from certification.models import Certification, QuizzCertification
from lab.tests import factories

from ..models import CertificationNotification, NotificationType

PATH_TO_COMPLETE = "path/to/complete"
PATH_TO_SUCCESS = "path/to/success"


@pytest.fixture(name="certification")
def certification_fixture():
    certification = Certification.objects.create(
        name="certification",
        invitation_to_complete_email_template_path=PATH_TO_COMPLETE,
        success_email_template_path=PATH_TO_SUCCESS,
    )
    QuizzCertification.objects.create(
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

    assert notification.get_context_for_certification() == {
        "quizz_link": certification.quizz.url,
        "passing_score": certification.quizz.passing_score,
        "email": notification.user.email,
    }


@pytest.mark.django_db
def test_get_context_for_success(certification: Certification):
    notification = CertificationNotification.objects.create(
        type_of=NotificationType.SUCCESS,
        certification=certification,
        user=factories.StaffUserFactory(),
    )

    assert notification.get_context_for_certification() == {}


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
