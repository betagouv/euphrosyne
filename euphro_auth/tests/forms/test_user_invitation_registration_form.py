from django.test import TestCase

from euphro_auth.models import User

from ...forms import UserInvitationRegistrationForm


class TestUserInvitationRegistrationForm(TestCase):
    def test_email_can_be_the_same_as_user(self):
        user = User.objects.create(email="test@test.test")
        form = UserInvitationRegistrationForm(
            data={
                "email": "test@test.test",
                "new_password1": "abcdef102",
                "new_password2": "abcdef102",
            },
            user=user,
        )

        self.assertTrue(form.is_valid())

    def test_email_should_be_unique(self):
        user = User.objects.create(email="test@test.test")
        User.objects.create(email="anotheruser@test.test")
        form = UserInvitationRegistrationForm(
            data={
                "email": "anotheruser@test.test",
                "new_password1": "abcdef102",
                "new_password2": "abcdef102",
            },
            user=user,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)
        self.assertEqual(
            form.errors["email"][0],
            "An account with this email already exists.",
        )
