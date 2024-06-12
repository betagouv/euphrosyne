from io import StringIO
from unittest import mock

from django.core import mail
from django.core.management import call_command
from django.test import TestCase

from certification.certifications.models import Certification, QuizzCertification
from lab.tests.factories import StaffUserFactory

from ..models import CertificationNotification, NotificationType

TEMPLATE = "certification/email/radioprotection_invitation.html"


class ClosepollTest(TestCase):
    def test_command_send_notification(self):
        user = StaffUserFactory()
        notification = CertificationNotification.objects.create(
            user=user,
            certification=Certification.objects.create(
                name="certification",
                invitation_to_complete_email_template_path=TEMPLATE,
            ),
            type_of=NotificationType.INVITATION_TO_COMPLETE,
        )
        QuizzCertification.objects.create(
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

    def test_command_continue_if_error(self):
        certification = Certification.objects.create(
            name="certification",
            invitation_to_complete_email_template_path=TEMPLATE,
        )
        QuizzCertification.objects.create(
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
