from unittest.mock import patch

from django.db.models.query import QuerySet
from django.test.testcases import SimpleTestCase

from ...forms import UserSendInvitationForm
from ...models import UserInvitation


class TestUserSendInvitationForm(SimpleTestCase):
    def test_email_should_be_unique(self):
        form = UserSendInvitationForm(data={"email": "test@test.test"})

        with patch.object(QuerySet, "exists", return_value=True):
            self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)
        self.assertEqual(form.errors["email"][0], "This user has already been invited.")

    def test_user_creation(self):
        form = UserSendInvitationForm(data={"email": "test@test.test"})
        with patch.object(QuerySet, "exists", return_value=False):
            self.assertTrue(form.is_valid())
        user_invitation: UserInvitation = form.save(commit=False)

        self.assertTrue(user_invitation)
        self.assertTrue(user_invitation.user)
        self.assertEqual(user_invitation.user.email, "test@test.test")
        self.assertFalse(user_invitation.user.invitation_completed)
        self.assertTrue(user_invitation.user.is_staff)
