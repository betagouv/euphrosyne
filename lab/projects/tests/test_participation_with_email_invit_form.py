from unittest import mock

from django.contrib.auth import get_user_model
from django.core import mail
from django.forms.models import BaseModelForm
from django.test import SimpleTestCase

from lab.models import Participation
from lab.projects.models import Project

from ..forms import BaseParticipationForm


class TestBaseParticipationForm(SimpleTestCase):
    def test_send_email_on_save(self):
        member = get_user_model()(id=2, email="member@test.com", password="test")
        project = Project(id=1, name="Test project")
        form = BaseParticipationForm(data={"project": project.id, "user": member.id})
        with mock.patch.object(
            BaseModelForm,
            "save",
            return_value=Participation(id=1, user=member, project=project),
        ):
            form.save(commit=False)

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to[0], member.email)
