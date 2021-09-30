from django.contrib.auth import get_user_model
from django.test import TestCase

from ...forms import UserInvitationRegistrationForm


class TestUserInvitationRegistrationForm(TestCase):
    def test_email_can_be_the_same_as_user(self):
        user = get_user_model().objects.create(email="test@test.test")
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
        user = get_user_model().objects.create(email="test@test.test")
        get_user_model().objects.create(email="anotheruser@test.test")
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

    def test_complete_invitation_on_save(self):
        user = get_user_model().objects.create(email="test@test.test")
        form = UserInvitationRegistrationForm(
            data={
                "email": "test@test.test",
                "new_password1": "abcdef102",
                "new_password2": "abcdef102",
            },
            user=user,
        )

        form.is_valid()
        form.save()
        self.assertTrue(user.invitation_completed)
