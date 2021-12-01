from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import RequestFactory
from django.test.testcases import TestCase
from django.urls import reverse
from django.utils import timezone

from euphro_auth.models import UserInvitation

from ...admin import UserInvitationAdmin


class MockedMessages(list):
    def add(self, level, message, extra_tags=None, fail_silently=False):
        self.append((level, message, extra_tags, fail_silently))


class TestSendInvitationMailAction(TestCase):
    def setUp(self):
        self.request_factory = RequestFactory()
        self.model_admin = UserInvitationAdmin(UserInvitation, AdminSite())
        admin_user = get_user_model()(
            email="admin@test.test", is_staff=True, is_lab_admin=True
        )
        self.request = self.request_factory.get(
            reverse("admin:euphro_auth_userinvitation_changelist")
        )
        self.request.user = admin_user
        # pylint: disable=protected-access
        self.request._messages = MockedMessages()
        self.pending_registration_user = get_user_model().objects.create(
            email="pending@test.test", is_staff=True
        )
        self.registered_user = get_user_model().objects.create(
            email="registered@test.test",
            is_staff=True,
            invitation_completed_at=timezone.datetime(2021, 11, 22),
        )

    def test_send_email_to_non_registered_users(self):
        actions = self.model_admin.get_actions(self.request)
        actions["send_invitation_mail_action"][0](
            self.model_admin, self.request, UserInvitation.objects.all()
        )
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to[0], self.pending_registration_user.email
