from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core import mail
from django.test import Client, TestCase
from django.urls import reverse

from euphro_auth.models import UserGroups


class TestUserInvitationAdmin(TestCase):
    fixtures = [
        "groups",
    ]

    def setUp(self):
        self.client = Client()
        self.admin_user = get_user_model().objects.create_user(
            email="admin_user@test.com", password="admin_user", is_staff=True
        )
        self.admin_user.groups.add(Group.objects.get(name=UserGroups.ADMIN.value))
        self.view_url = reverse("admin:euphro_auth_userinvitation_add")

    def test_user_invitation_get(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(self.view_url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(
            response,
            '<input type="email" name="email" \
                 autocomplete="email" maxlength="254" required="" id="id_email">',
            html=True,
        )

    def test_user_invitation_post_success(self):
        self.client.force_login(self.admin_user)
        self.client.post(self.view_url, data={"email": "test@test.test"})
        user = get_user_model().objects.get(email="test@test.test")
        self.assertFalse(user.invitation_completed)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "[Euphrosyne] Invitation to register")
