from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase

from ...forms import UserSendInvitationForm
from ...models import UserInvitation


class TestUserSendInvitationForm(TestCase):
    def test_email_should_be_unique(self):
        get_user_model().objects.create(email="test@test.test")
        form = UserSendInvitationForm(data={"email": "test@test.test"})

        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)
        self.assertEqual(form.errors["email"][0], "This user has already been invited.")

    def test_user_creation(self):
        form = UserSendInvitationForm(data={"email": "test@test.test"})
        self.assertTrue(form.is_valid())
        user_invitation: UserInvitation = form.save()

        self.assertTrue(user_invitation)
        self.assertTrue(user_invitation.id)
        self.assertTrue(user_invitation.user)
        self.assertEqual(user_invitation.user.email, "test@test.test")
        self.assertFalse(user_invitation.user.invitation_completed)

    def test_email_sending(self):
        form = UserSendInvitationForm(data={"email": "test@test.test"})
        form.is_valid()
        form.save()

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "[Euphrosyne] Invitation to register")
