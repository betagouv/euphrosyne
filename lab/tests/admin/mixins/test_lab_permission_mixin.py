from typing import Optional

from django.contrib.admin import ModelAdmin
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase

from ....admin.mixins import LabPermission, LabPermissionMixin, LabRole
from ....models import Project


class TestModelAdmin(LabPermissionMixin, ModelAdmin):
    def get_related_project(self, obj: Project = None) -> Optional[Project]:
        return obj


class TestLabPermissionMixin(TestCase):
    def setUp(self):
        self.admin_user = get_user_model().objects.create(
            email="admin@test.test", is_staff=True, is_lab_admin=True
        )
        self.leader_user = get_user_model().objects.create(
            email="leader@test.test", is_staff=True
        )
        self.member_user = get_user_model().objects.create(
            email="member@test.test", is_staff=True
        )
        self.non_participant_user = get_user_model().objects.create(
            email="someuser@test.test", is_staff=True
        )
        self.project = Project.objects.create(name="Test project")
        self.project.participation_set.create(user=self.leader_user, is_leader=True)
        self.project.participation_set.create(user=self.member_user, is_leader=False)

        self.request_factory = RequestFactory()
        self.model_admin = TestModelAdmin(model=Project, admin_site=AdminSite())

    def test_default_permission_is_lab_admin(self):
        admin_request = self.request_factory.get("/someurl")
        admin_request.user = self.admin_user
        leader_request = self.request_factory.get("/someurl")
        leader_request.user = self.leader_user

        assert self.model_admin.has_view_permission(admin_request, self.project)
        assert self.model_admin.has_change_permission(admin_request, self.project)
        assert self.model_admin.has_delete_permission(admin_request, self.project)
        assert self.model_admin.has_add_permission(admin_request, self.project)

        assert not self.model_admin.has_view_permission(leader_request, self.project)
        assert not self.model_admin.has_change_permission(leader_request, self.project)
        assert not self.model_admin.has_delete_permission(leader_request, self.project)
        assert not self.model_admin.has_add_permission(leader_request, self.project)

    def test_users_with_higher_permission_can_do_action(self):
        non_participant_request = self.request_factory.get("/someurl")
        non_participant_request.user = self.non_participant_user

        member_request = self.request_factory.get("/someurl")
        member_request.user = self.member_user

        leader_request = self.request_factory.get("/someurl")
        leader_request.user = self.leader_user

        admin_request = self.request_factory.get("/someurl")
        admin_request.user = self.admin_user

        self.model_admin.lab_permissions = LabPermission(
            add_permission=LabRole.PROJECT_LEADER,
            change_permission=LabRole.PROJECT_LEADER,
            delete_permission=LabRole.PROJECT_LEADER,
            view_permission=LabRole.PROJECT_LEADER,
        )

        assert not self.model_admin.has_view_permission(
            non_participant_request, self.project
        )
        assert not self.model_admin.has_change_permission(
            non_participant_request, self.project
        )
        assert not self.model_admin.has_delete_permission(
            non_participant_request, self.project
        )
        assert not self.model_admin.has_add_permission(
            non_participant_request, self.project
        )

        assert not self.model_admin.has_view_permission(member_request, self.project)
        assert not self.model_admin.has_change_permission(member_request, self.project)
        assert not self.model_admin.has_delete_permission(member_request, self.project)
        assert not self.model_admin.has_add_permission(member_request, self.project)

        assert self.model_admin.has_view_permission(leader_request, self.project)
        assert self.model_admin.has_change_permission(leader_request, self.project)
        assert self.model_admin.has_delete_permission(leader_request, self.project)
        assert self.model_admin.has_add_permission(leader_request, self.project)

        assert self.model_admin.has_view_permission(admin_request, self.project)
        assert self.model_admin.has_change_permission(admin_request, self.project)
        assert self.model_admin.has_delete_permission(admin_request, self.project)
        assert self.model_admin.has_add_permission(admin_request, self.project)

    def test_non_participant_permission(self):
        request = self.request_factory.get("/someurl")
        request.user = self.non_participant_user

        self.model_admin.lab_permissions = LabPermission(
            add_permission=LabRole.ANY_USER,
            change_permission=LabRole.ANY_USER,
            delete_permission=LabRole.ANY_USER,
            view_permission=LabRole.ANY_USER,
        )

        assert self.model_admin.has_view_permission(request, self.project)
        assert self.model_admin.has_change_permission(request, self.project)
        assert self.model_admin.has_delete_permission(request, self.project)
        assert self.model_admin.has_add_permission(request, self.project)

    def test_member_permission(self):
        request = self.request_factory.get("/someurl")
        request.user = self.member_user

        self.model_admin.lab_permissions = LabPermission(
            add_permission=LabRole.PROJECT_MEMBER,
            change_permission=LabRole.PROJECT_MEMBER,
            delete_permission=LabRole.PROJECT_MEMBER,
            view_permission=LabRole.PROJECT_MEMBER,
        )

        assert self.model_admin.has_view_permission(request, self.project)
        assert self.model_admin.has_change_permission(request, self.project)
        assert self.model_admin.has_delete_permission(request, self.project)
        assert self.model_admin.has_add_permission(request, self.project)

    def test_leader_permission(self):
        request = self.request_factory.get("/someurl")
        request.user = self.leader_user

        self.model_admin.lab_permissions = LabPermission(
            add_permission=LabRole.PROJECT_LEADER,
            change_permission=LabRole.PROJECT_LEADER,
            delete_permission=LabRole.PROJECT_LEADER,
            view_permission=LabRole.PROJECT_LEADER,
        )

        assert self.model_admin.has_view_permission(request, self.project)
        assert self.model_admin.has_change_permission(request, self.project)
        assert self.model_admin.has_delete_permission(request, self.project)
        assert self.model_admin.has_add_permission(request, self.project)

    def test_admin_permission(self):
        request = self.request_factory.get("/someurl")
        request.user = self.admin_user

        self.model_admin.lab_permissions = LabPermission(
            add_permission=LabRole.LAB_ADMIN,
            change_permission=LabRole.LAB_ADMIN,
            delete_permission=LabRole.LAB_ADMIN,
            view_permission=LabRole.LAB_ADMIN,
        )

        assert self.model_admin.has_view_permission(request, self.project)
        assert self.model_admin.has_change_permission(request, self.project)
        assert self.model_admin.has_delete_permission(request, self.project)
        assert self.model_admin.has_add_permission(request, self.project)
