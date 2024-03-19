from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import Client, TestCase
from django.test.client import RequestFactory
from django.urls import reverse
from django.utils.translation import gettext

from euphro_auth.models import UserInvitation

from ...admin import UserInvitationAdmin


class TestUserInvitationAdmin(TestCase):
    def setUp(self):
        self.request_factory = RequestFactory()
        self.client = Client()
        self.model_admin = UserInvitationAdmin(UserInvitation, AdminSite())
        self.admin_user = get_user_model().objects.create_user(
            email="admin_user@test.com",
            password="admin_user",
            is_staff=True,
            is_lab_admin=True,
        )
        self.view_url = reverse("admin:euphro_auth_userinvitation_add")
        self.client.force_login(self.admin_user)

    def test_add_user_invitation_creates_user_with_right_permissions(self):
        self.client.post(
            self.view_url,
            data={"email": "test@test.test", "first_name": "Test", "last_name": "Test"},
        )
        user = get_user_model().objects.get(email="test@test.test")
        assert user.is_staff

    def test_add_user_invitation_sends_invitation_email(self):
        self.client.post(
            self.view_url,
            data={"email": "test@test.test", "first_name": "Test", "last_name": "Test"},
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject, gettext("[Euphrosyne] Invitation to register")
        )

    def test_admin_user_can_view_invitations(self):
        request = self.request_factory.get(self.view_url)
        request.user = self.admin_user
        assert self.model_admin.has_module_permission(request)
        assert self.model_admin.has_view_permission(request, obj=None)

    def test_staff_user_can_not_view_invitations(self):
        user = get_user_model()(
            email="member@test.test", is_staff=True, is_lab_admin=False
        )
        request = self.request_factory.get(self.view_url)
        request.user = user
        assert not self.model_admin.has_module_permission(request)
        assert not self.model_admin.has_view_permission(request, obj=None)
