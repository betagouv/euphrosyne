from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase

from lab.models import Project

from ..models import Participation


class TestParticipationModel(TestCase):
    def test_user_can_participate_only_once_in_project(self):
        user = get_user_model().objects.create(
            email="user@test.test", password="password"
        )
        project = Project.objects.create(name="Project Test")
        Participation.objects.create(user=user, project=project)
        with self.assertRaises(IntegrityError):
            Participation.objects.create(user=user, project=project)

    def test_project_can_only_have_one_leader_participation(self):
        leader = get_user_model().objects.create(
            email="leader@test.test", password="password"
        )
        leader_wanabe = get_user_model().objects.create(
            email="leader2@test.test", password="password"
        )
        project = Project.objects.create(name="Project Test")
        Participation.objects.create(user=leader, project=project, is_leader=True)
        with self.assertRaises(IntegrityError):
            Participation.objects.create(
                user=leader_wanabe, project=project, is_leader=True
            )
