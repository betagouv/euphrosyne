from django.test import TestCase

from ...fields import ObjectGroupChoiceField
from ..factories import ObjectGroupFactory, RunFactory


class TestObjectGroupChoiceField(TestCase):
    def setUp(self):
        self.run = RunFactory()
        self.run_object_group = ObjectGroupFactory()
        self.run.run_object_groups.add(self.run_object_group)
        self.isolated_object_group = ObjectGroupFactory()

    def test_field_queryset_includes_group_without_run(self):
        field = ObjectGroupChoiceField(project_id=self.run.project_id)
        assert field.queryset.get(id=self.run_object_group.id)
        assert field.queryset.get(id=self.isolated_object_group.id)

    def test_field_choices_only_have_project_object_groups(self):
        field = ObjectGroupChoiceField(project_id=self.run.project_id)
        assert (self.run_object_group.id, str(self.run_object_group)) in field.choices
        assert (
            self.isolated_object_group.id,
            str(self.isolated_object_group),
        ) not in field.choices
