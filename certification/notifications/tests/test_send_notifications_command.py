from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock
import pytest
from django.core import mail
from django.core.management import call_command

from certification.certifications.models import Certification, QuizCertification
from lab.tests.factories import StaffUserFactory

from ..models import CertificationNotification, NotificationType


@pytest.fixture(name="temp_template_path")
def temp_template_path_fixture():
    """Create a temporary directory with a template file for testing."""
    with TemporaryDirectory() as temp_dir:
        # Create the template directory structure
        template_dir = Path(temp_dir) / "certification" / "email"
        template_dir.mkdir(parents=True)

        # Create a simple template file
        template_path = template_dir / "radioprotection_invitation.html"
        template_path.write_text("<html><body>Test template</body></html>")

        # Add the temp directory to template dirs
        with mock.patch(
            "django.template.loaders.filesystem.Loader.get_dirs"
        ) as mock_get_dirs:
            mock_get_dirs.return_value = [temp_dir]
            yield str(template_path)


@pytest.mark.django_db
def test_command_send_notification(temp_template_path: str):
    user = StaffUserFactory()
    notification = CertificationNotification.objects.create(
        user=user,
        certification=Certification.objects.create(
            name="certification",
            invitation_to_complete_email_template_path=temp_template_path,
        ),
        type_of=NotificationType.INVITATION_TO_COMPLETE,
    )
    QuizCertification.objects.create(
        certification=notification.certification, url="url", passing_score=1
    )

    out = StringIO()
    call_command("send_notifications", stdout=out)

    notification.refresh_from_db()
    assert notification.is_sent

    assert (
        f"Notification for certification certification sent to {user.email}."
        in out.getvalue()
    )

    assert len(mail.outbox) == 1
    assert mail.outbox[0].recipients() == [user.email]


@pytest.mark.django_db
def test_command_continue_if_error(temp_template_path: str):
    certification = Certification.objects.create(
        name="certification",
        invitation_to_complete_email_template_path=temp_template_path,
    )
    QuizCertification.objects.create(
        certification=certification, url="url", passing_score=1
    )

    notifications = []
    with mock.patch(
        # pylint: disable=line-too-long
        "certification.management.commands.send_notifications.CertificationNotification.send_notification"
    ) as mock_fn:
        mock_fn.side_effect = [Exception("Error"), None]
        users = [StaffUserFactory(), StaffUserFactory()]
        for user in users:
            notifications.append(
                CertificationNotification.objects.create(
                    user=user,
                    certification=certification,
                    type_of=NotificationType.INVITATION_TO_COMPLETE,
                )
            )

        out = StringIO()
        call_command("send_notifications", stdout=out)

        for notification in notifications:
            notification.refresh_from_db()

        assert not notifications[0].is_sent
        assert notifications[1].is_sent
