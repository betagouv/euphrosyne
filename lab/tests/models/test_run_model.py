from django.core.exceptions import ValidationError
from django.test import TestCase

from ...models import Project, Run
from ..factories import RunFactory


class TestRunModelValidations(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name="Project Test")

    def test_can_be_empty_if_not_started(self):
        empty_run = RunFactory(status=Run.RunStatuses.NOT_STARTED)
        try:
            empty_run.full_clean()
        except ValidationError:
            self.fail("Run not started and empty raised a ValidationError")

    def test_cant_be_empty_if_started(self):
        empty_run = RunFactory(status=Run.RunStatuses.STARTED)
        with self.assertRaises(ValidationError):
            empty_run.full_clean()

    def test_cant_be_empty_if_finished(self):
        empty_run = RunFactory(status=Run.RunStatuses.FINISHED)
        with self.assertRaises(ValidationError):
            empty_run.full_clean()
