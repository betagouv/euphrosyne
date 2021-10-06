from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db.models.query import QuerySet
from django.test import SimpleTestCase

from ...forms import UserInvitationRegistrationForm


class TestUserInvitationRegistrationForm(SimpleTestCase):
    def test_email_can_be_the_same_as_user(self):
        user = get_user_model()(email="test@test.test")
        form = UserInvitationRegistrationForm(
            data={
                "email": "test@test.test",
                "new_password1": "abcdef102",
                "new_password2": "abcdef102",
            },
            user=user,
        )

        self.assertTrue(form.is_valid())

    def test_email_can_be_changed(self):
        user = get_user_model()(email="test@test.test")
        form = UserInvitationRegistrationForm(
            data={
                "email": "new_email@test.test",
                "new_password1": "abcdef102",
                "new_password2": "abcdef102",
            },
            user=user,
        )

        with patch.object(QuerySet, "exists", return_value=False):
            self.assertTrue(form.is_valid())
        form.save(commit=False)
        self.assertEqual(user.email, "new_email@test.test")

    def test_email_should_be_unique(self):
        user = get_user_model()(email="test@test.test")
        form = UserInvitationRegistrationForm(
            data={
                "email": "anotheruser@test.test",
                "new_password1": "abcdef102",
                "new_password2": "abcdef102",
            },
            user=user,
        )
        with patch.object(QuerySet, "exists", return_value=True):
            self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)
        self.assertEqual(
            form.errors["email"][0],
            "An account with this email already exists.",
        )

    def test_complete_invitation_on_save(self):
        user = get_user_model()(email="test@test.test")
        form = UserInvitationRegistrationForm(
            data={
                "email": "test@test.test",
                "new_password1": "abcdef102",
                "new_password2": "abcdef102",
            },
            user=user,
        )
        with patch.object(QuerySet, "exists", return_value=False):
            form.is_valid()
        form.save(commit=False)
        self.assertTrue(user.invitation_completed)
