from django.contrib.auth import get_user_model
from django.test.testcases import TestCase

from ...forms import ChangeLeaderForm
from ...models import Project


class TestParticipationLeaderForm(TestCase):
    # pylint: disable=no-self-use
    def test_populates_form(self):
        project = Project.objects.create(name="Test project")
        participation = project.participation_set.create(
            user=get_user_model().objects.create(email="leader@test.test"),
            is_leader=True,
        )
        form = ChangeLeaderForm(project=project)
        assert list(form.fields["leader_participation"].choices)[1][1] == str(
            participation
        )
        assert form.initial["leader_participation"] == project.leader
