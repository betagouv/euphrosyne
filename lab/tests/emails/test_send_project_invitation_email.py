from django.conf import settings
from django.core import mail
from django.test import TestCase

from euphro_auth.tests.factories import StaffUserFactory
from lab.models import Project

from ...emails import send_project_invitation_email


class TestSendProjectInvitationEmail(TestCase):
    def test_send_email(self):
        project = Project(id=1, name="Test Project")
        user = StaffUserFactory()

        send_project_invitation_email(
            email=user.email,
            project=project,
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject,
            "Invitation à rejoindre le projet AGLAE Test Project",
        )
        self.assertIn(
            f"{settings.SITE_URL}/lab/project/{project.id}/change/",
            mail.outbox[0].body,
        )
