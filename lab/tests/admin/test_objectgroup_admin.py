from django.contrib.admin.sites import AdminSite
from django.test import TestCase
from django.test.client import RequestFactory
from django.urls import reverse

from lab.models.run import ObjectGroup

from ...admin import ObjectGroupAdmin
from .. import factories


class TesObjectGroupAdminPermissions(TestCase):
    def setUp(self):
        self.run_admin = ObjectGroupAdmin(model=ObjectGroup, admin_site=AdminSite())
        self.run = factories.RunFactory(project=factories.ProjectWithLeaderFactory())
        self.member = self.run.project.members.first()
        self.object_group = factories.ObjectGroupFactory()
        self.object_group.runs.add(self.run)

    def test_change_objectgroup_is_allowed_if_project_member(self):
        request = RequestFactory().get(
            reverse("admin:lab_objectgroup_change", args=[self.object_group.id])
        )
        request.user = self.member
        assert self.run_admin.has_change_permission(request, self.object_group)

    def test_change_objectgroup_is_forbidden_for_non_participant(self):
        user = factories.StaffUserFactory()
        request = RequestFactory().get(
            reverse("admin:lab_objectgroup_change", args=[self.object_group.id])
        )
        request.user = user
        assert not self.run_admin.has_change_permission(request, self.object_group)
