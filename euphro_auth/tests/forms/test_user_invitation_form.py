from django.core import mail
from django.test import TestCase

from euphro_auth.models import User

from ...forms import UserInvitationForm
from ...models import UserInvitation


class TestUserInvitationForm(TestCase):
    def test_email_should_be_unique(self):
        User.objects.create(email="test@test.test")
        form = UserInvitationForm(data={"email": "test@test.test"})

        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)
        self.assertEqual(form.errors["email"][0], "This user has already been invited.")

    def test_user_creation(self):
        form = UserInvitationForm(data={"email": "test@test.test"})
        self.assertTrue(form.is_valid())
        user_invitation: UserInvitation = form.save()

        self.assertTrue(user_invitation)
        self.assertFalse(user_invitation.completed)
        self.assertTrue(user_invitation.id)
        self.assertTrue(user_invitation.user)
        self.assertTrue(user_invitation.user.email, "test@test.test")

    def test_email_sending(self):
        form = UserInvitationForm(data={"email": "test@test.test"})
        form.is_valid()
        form.save()

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "[Euphrosyne] Invitation to register")
