from django.test import TestCase
from django.utils import timezone

from ...models import Project
from .. import factories


class TestProjectModel(TestCase):
    def test_status_is_to_schedule_by_default(self):
        project = factories.ProjectFactory()
        assert project.status == Project.Status.TO_SCHEDULE

    def test_status_is_scheduled_when_one_run_with_start_date(self):
        run = factories.RunFactory(
            start_date=timezone.now() + timezone.timedelta(days=1),
            end_date=timezone.now() + timezone.timedelta(days=2),
        )
        assert run.project.status == Project.Status.SCHEDULED

    def test_status_is_ongoing_when_run_with_start_date_before_now(self):
        run = factories.RunFactory(
            start_date=timezone.now() - timezone.timedelta(days=1),
            end_date=timezone.now() + timezone.timedelta(days=1),
        )
        assert run.project.status == Project.Status.ONGOING

    def test_status_is_finished_when_run_with_end_date_before_now(self):
        run = factories.RunFactory(
            start_date=timezone.now() - timezone.timedelta(days=2),
            end_date=timezone.now() - timezone.timedelta(days=1),
        )
        assert run.project.status == Project.Status.FINISHED
