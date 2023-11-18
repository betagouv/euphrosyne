from django.test import TestCase
from django.utils import timezone

from ...models import Project
from ..factories import ProjectFactory


class ProjectModelTestCase(TestCase):
    def test_project_only_finished(self):
        finished_project = ProjectFactory(name="Test Project")
        finished_project.runs.create(
            start_date=timezone.now() - timezone.timedelta(days=2),
            end_date=timezone.now() - timezone.timedelta(days=1),
        )
        not_finished_project = ProjectFactory(name="Not Finished Project")
        not_finished_project.runs.create(
            start_date=timezone.now() - timezone.timedelta(days=1),
            end_date=timezone.now() + timezone.timedelta(days=1),
        )
        self.assertEqual(Project.objects.only_finished().count(), 1)

    def test_project_only_public(self):
        Project.objects.create(name="Public Project", confidential=False)
        Project.objects.create(name="Confidential Project", confidential=True)
        self.assertEqual(Project.objects.only_public().count(), 1)
