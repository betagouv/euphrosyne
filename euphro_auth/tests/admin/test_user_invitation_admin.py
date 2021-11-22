from django.contrib.auth import get_user_model
from django.core import mail
from django.test import Client, TestCase
from django.urls import reverse


class TestUserInvitationAdmin(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = get_user_model().objects.create_user(
            email="admin_user@test.com",
            password="admin_user",
            is_staff=True,
            is_lab_admin=True,
        )
        self.view_url = reverse("admin:euphro_auth_userinvitation_add")
        self.client.force_login(self.admin_user)

    def test_add_user_invitation_creates_user_with_right_permissions(self):
        self.client.post(self.view_url, data={"email": "test@test.test"})
        user = get_user_model().objects.get(email="test@test.test")
        assert user.is_staff

    def test_add_user_invitation_sends_invitation_email(self):
        self.client.post(self.view_url, data={"email": "test@test.test"})
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "[Euphrosyne] Invitation to register")
