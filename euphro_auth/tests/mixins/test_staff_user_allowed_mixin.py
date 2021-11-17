from django.contrib.admin import ModelAdmin
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.test import SimpleTestCase
from django.test.client import RequestFactory

from ...mixins import StaffUserAllowedMixin


class TestStaffUserAllowedMixin(SimpleTestCase):
    class TestModelAdmin(StaffUserAllowedMixin, ModelAdmin):
        pass

    def setUp(self):
        self.staff_user = get_user_model()(email="staff@test.test", is_staff=True)
        self.other_user = get_user_model()(email="user@test.test")
        self.request_factory = RequestFactory()
        self.model_admin = self.TestModelAdmin(
            model=get_user_model(), admin_site=AdminSite()
        )

    def test_staff_user_has_module_permission(self):
        request = self.request_factory.get("/someurl")
        request.user = self.staff_user

        assert self.model_admin.has_module_permission(request)

    def test_staff_user_has_view_permission(self):
        request = self.request_factory.get("/someurl")
        request.user = self.staff_user

        assert self.model_admin.has_view_permission(request)

    def test_basic_user_has_no_module_permission(self):
        request = self.request_factory.get("/someurl")
        request.user = self.other_user

        assert not self.model_admin.has_module_permission(request)

    def test_basic_user_has_no_view_permission(self):
        request = self.request_factory.get("/someurl")
        request.user = self.other_user

        assert not self.model_admin.has_view_permission(request)
