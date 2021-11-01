from django.contrib.auth import get_user_model
from django.test import TestCase

from ...models import Participation, Project


#  pylint: disable=no-self-use
class TestProjectModel(TestCase):
    def test_project_leader_property(self):
        user = get_user_model().objects.create(
            email="user@test.test", password="password"
        )
        project = Project.objects.create(name="Project Test")
        Participation.objects.create(user=user, project=project, is_leader=True)

        assert project.leader
        assert project.leader.user_id == user.id
        assert isinstance(project.leader, Participation)

    def test_project_leader_property_returns_none(self):
        user = get_user_model().objects.create(
            email="user@test.test", password="password"
        )
        project = Project.objects.create(name="Project Test")
        Participation.objects.create(user=user, project=project)

        assert project.leader is None
