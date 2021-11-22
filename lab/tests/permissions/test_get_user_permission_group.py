from django.contrib.auth import get_user_model
from django.test import TestCase
from django.test.client import RequestFactory

from lab.models import Project

from ...permissions import LabRole, get_user_permission_group


class TestGetUserPermissionGroup(TestCase):
    def setUp(self):
        request_factory = RequestFactory()
        self.request = request_factory.get("/")
        self.project = Project.objects.create(name="Test project")

    def test_get_admin_user_permission(self):
        admin_user = get_user_model().objects.create(
            email="admin@test.test", is_staff=True, is_lab_admin=True
        )
        self.request.user = admin_user

        assert (
            get_user_permission_group(self.request, self.project) == LabRole.LAB_ADMIN
        )

    def test_get_leader_permission(self):
        leader_user = get_user_model().objects.create(
            email="admin@test.test", is_staff=True
        )
        self.project.participation_set.create(user=leader_user, is_leader=True)
        self.request.user = leader_user

        assert (
            get_user_permission_group(self.request, self.project)
            == LabRole.PROJECT_LEADER
        )

    def test_get_member_permission(self):
        member_user = get_user_model().objects.create(
            email="admin@test.test", is_staff=True
        )
        self.project.participation_set.create(user=member_user)
        self.request.user = member_user

        assert (
            get_user_permission_group(self.request, self.project)
            == LabRole.PROJECT_MEMBER
        )

    def test_get_staff_user_permission(self):
        staff_user = get_user_model().objects.create(
            email="admin@test.test", is_staff=True
        )
        self.request.user = staff_user

        assert (
            get_user_permission_group(self.request, self.project)
            == LabRole.ANY_STAFF_USER
        )
