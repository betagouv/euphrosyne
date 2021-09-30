from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse


class UserInvitationAdmin(TestCase):
    def setUp(self):
        self.client = Client()
        self.superuser = get_user_model().objects.create_superuser(
            email="superuser@test.com", password="superuser"
        )

    def test_user_invitation_get(self):
        admin_invitation_creation_url = reverse("admin:euphro_auth_userinvitation_add")

        self.client.force_login(self.superuser)
        response = self.client.get(admin_invitation_creation_url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(
            response,
            '<input type="email" name="email" \
                 autocomplete="email" maxlength="254" required="" id="id_email">',
            html=True,
        )

    def test_user_invitation_post_success(self):
        admin_invitation_creation_url = reverse("admin:euphro_auth_userinvitation_add")

        self.client.force_login(self.superuser)
        self.client.post(
            admin_invitation_creation_url, data={"email": "test@test.test"}
        )
        self.assertTrue(get_user_model().objects.get(email="test@test.test"))
