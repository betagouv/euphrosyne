from django.contrib.auth import get_user_model
from django.forms import ValidationError
from django.test import TestCase
from slugify import slugify

from lab.models import Participation

from ..models import Project


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

    def test_project_slug_is_saved(self):
        project = Project.objects.create(name="Project Test")
        assert project.slug
        assert project.slug == slugify(project.name)

    def test_clean_new_project_with_slug_field(self):
        # Create project 1
        Project.objects.create(name="Project Test")
        # Init a project with a slug identic to project 1
        project = Project(name="Project test")
        # Clean it, it should raise ValidationError
        with self.assertRaises(ValidationError):
            project.clean()
