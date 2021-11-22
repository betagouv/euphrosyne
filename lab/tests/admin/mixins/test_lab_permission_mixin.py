from typing import Optional
from unittest.mock import patch

from django.contrib.admin import ModelAdmin
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.test import RequestFactory, SimpleTestCase

from ....admin.mixins import LabPermission, LabPermissionMixin, LabRole
from ....models import Project


class TestModelAdmin(LabPermissionMixin, ModelAdmin):
    def get_related_project(self, obj: Project = None) -> Optional[Project]:
        return obj


class TestLabPermissionMixin(SimpleTestCase):
    def setUp(self):
        self.project = Project(name="Test project")

        self.request_factory = RequestFactory()
        self.model_admin = TestModelAdmin(model=Project, admin_site=AdminSite())

    def test_admin_default_to_admin_permissions(self):
        assert self.model_admin.lab_permissions.add_permission == LabRole.LAB_ADMIN
        assert self.model_admin.lab_permissions.change_permission == LabRole.LAB_ADMIN
        assert self.model_admin.lab_permissions.delete_permission == LabRole.LAB_ADMIN
        assert self.model_admin.lab_permissions.view_permission == LabRole.LAB_ADMIN

    @patch(
        "lab.permissions.get_user_permission_group",
        return_value=LabRole.LAB_ADMIN,
    )
    def test_users_with_higher_or_equal_permission_are_allowed(self, _):
        self.model_admin.lab_permissions = LabPermission(
            add_permission=LabRole.LAB_ADMIN,
            change_permission=LabRole.LAB_ADMIN,
            delete_permission=LabRole.LAB_ADMIN,
            view_permission=LabRole.LAB_ADMIN,
        )
        admin_request = self.request_factory.get("/someurl")
        admin_request.user = get_user_model()(is_staff=True, is_lab_admin=True)
        leader_request = self.request_factory.get("/someurl")
        leader_request.user = get_user_model()(is_staff=True)

        assert self.model_admin.has_view_permission(admin_request, self.project)
        assert self.model_admin.has_change_permission(admin_request, self.project)
        assert self.model_admin.has_delete_permission(admin_request, self.project)
        assert self.model_admin.has_add_permission(admin_request, self.project)

    @patch(
        "lab.permissions.get_user_permission_group",
        return_value=LabRole.PROJECT_LEADER,
    )
    def test_users_with_less_permission_are_restricted(self, _):
        request = self.request_factory.get("/someurl")
        request.user = get_user_model()(is_staff=True)
        assert not self.model_admin.has_view_permission(request, self.project)
        assert not self.model_admin.has_change_permission(request, self.project)
        assert not self.model_admin.has_delete_permission(request, self.project)
        assert not self.model_admin.has_add_permission(request, self.project)
