from django.contrib.admin import ModelAdmin
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.test import SimpleTestCase
from django.test.client import RequestFactory

from ....admin.mixins import LabAdminAllowedMixin


class TestLabAdminAllowedMixin(SimpleTestCase):
    class TestModelAdmin(LabAdminAllowedMixin, ModelAdmin):
        pass

    def setUp(self):
        self.lab_admin_user = get_user_model()(
            email="admin@test.test", is_staff=True, is_lab_admin=True
        )
        self.staff_user = get_user_model()(email="staff@test.test", is_staff=True)
        self.request_factory = RequestFactory()
        self.model_admin = self.TestModelAdmin(
            model=get_user_model(), admin_site=AdminSite()
        )

    def test_admin_user_has_permissions(self):
        request = self.request_factory.get("/someurl")
        request.user = self.lab_admin_user

        assert self.model_admin.has_module_permission(request)
        assert self.model_admin.has_add_permission(request)
        assert self.model_admin.has_change_permission(request)
        assert self.model_admin.has_view_permission(request)
        assert self.model_admin.has_delete_permission(request)

    def test_staff_user_does_not_have_permission(self):
        request = self.request_factory.get("/someurl")
        request.user = self.staff_user

        assert not self.model_admin.has_module_permission(request)
        assert not self.model_admin.has_add_permission(request)
        assert not self.model_admin.has_change_permission(request)
        assert not self.model_admin.has_view_permission(request)
        assert not self.model_admin.has_delete_permission(request)
