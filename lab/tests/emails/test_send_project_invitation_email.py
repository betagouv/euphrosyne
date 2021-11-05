from django.conf import settings
from django.core import mail
from django.test import SimpleTestCase

from lab.models import Project

from ...emails import send_project_invitation_email


class TestSendProjectInvitationEmail(SimpleTestCase):
    def test_send_email(self):
        project = Project(id=1, name="Test Project")

        send_project_invitation_email(
            email="test@test.com",
            project=project,
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject,
            f"[Euphrosyne] Invitation to join project {project.name}",
        )
        self.assertIn(
            f"{settings.SITE_URL}/admin/lab/project/{project.id}/change/",
            mail.outbox[0].body,
        )
