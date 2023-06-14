import json
from unittest import mock

from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory, TestCase
from django.urls import reverse

from lab.tests import factories

from ..admin import ObjectGroupAdmin
from ..forms import ObjectGroupForm, ObjectGroupImportC2RMFReadonlyForm
from ..models import ObjectGroup

CHANGE_VIEWNAME = "admin:lab_objectgroup_change"
ADD_VIEWNAME = "admin:lab_objectgroup_add"


class TesObjectGroupAdminPermissions(TestCase):
    def setUp(self):
        self.objectgroup_admin = ObjectGroupAdmin(
            model=ObjectGroup, admin_site=AdminSite()
        )
        self.run = factories.RunFactory(project=factories.ProjectWithLeaderFactory())
        self.member = self.run.project.members.first()
        self.object_group = factories.ObjectGroupFactory()
        self.object_group.runs.add(self.run)

    def test_change_objectgroup_is_allowed_if_project_member(self):
        request = RequestFactory().get(
            reverse(CHANGE_VIEWNAME, args=[self.object_group.id])
        )
        request.user = self.member
        assert self.objectgroup_admin.has_change_permission(request, self.object_group)

    def test_change_objectgroup_is_forbidden_for_non_participant(self):
        user = factories.StaffUserFactory()
        request = RequestFactory().get(
            reverse(CHANGE_VIEWNAME, args=[self.object_group.id])
        )
        request.user = user
        assert not self.objectgroup_admin.has_change_permission(
            request, self.object_group
        )


class TestObjectGroupAdminBehavior(TestCase):
    def setUp(self):
        self.objectgroup_admin = ObjectGroupAdmin(
            model=ObjectGroup, admin_site=AdminSite()
        )
        self.run = factories.RunFactory(project=factories.ProjectWithLeaderFactory())
        self.member = self.run.project.members.first()
        self.object_group = factories.ObjectGroupFactory()

    def test_save_run_relationship_when_specified_in_popup_when_adding(self):
        request = RequestFactory().post(
            reverse(ADD_VIEWNAME) + f"?run={self.run.id}", {"_popup": 1}
        )
        request.user = self.member
        self.objectgroup_admin.save_model(
            request, self.object_group, ObjectGroupForm(), change=False
        )
        self.object_group.refresh_from_db()

        assert self.object_group.runs.filter(id=self.run.id).exists()

    def test_saving_run_relationship_is_ignored_when_run_does_not_exist(self):
        request = RequestFactory().post(
            reverse(ADD_VIEWNAME) + "?run=-23", {"_popup": 1}
        )
        request.user = self.member
        self.objectgroup_admin.save_model(
            request, self.object_group, ObjectGroupForm(), change=False
        )
        self.object_group.refresh_from_db()

        assert not self.object_group.runs.exists()

    def test_saving_run_relationship_is_ignored_on_change(self):
        request = RequestFactory().post(
            reverse(CHANGE_VIEWNAME, args=[self.object_group.id])
            + f"?run={self.run.id}",
            {"_popup": 1},
        )
        request.user = self.member
        self.objectgroup_admin.save_model(
            request, self.object_group, ObjectGroupForm(), change=True
        )
        self.object_group.refresh_from_db()

        assert not self.object_group.runs.exists()

    def test_saving_run_relationship_is_ignored_when_not_popup(self):
        request = RequestFactory().post(
            reverse(ADD_VIEWNAME) + f"?run={self.run.id}",
        )
        request.user = self.member
        self.objectgroup_admin.save_model(
            request, self.object_group, ObjectGroupForm(), change=True
        )
        self.object_group.refresh_from_db()

        assert not self.object_group.runs.exists()

    def test_response_add_add_context_in_popup_post(self):
        run = factories.RunFactory(project=factories.ProjectWithLeaderFactory())
        self.object_group.runs.add(run)
        request = RequestFactory().post(
            reverse(ADD_VIEWNAME) + f"?run={self.run.id}",
            {"_popup": 1},
        )
        request.user = self.member
        response = self.objectgroup_admin.response_add(request, self.object_group)

        popup_response_data = json.loads(response.context_data["popup_response_data"])
        assert "objectgroup_run_run_ids" in popup_response_data
        assert popup_response_data["objectgroup_run_run_ids"] == [
            [self.object_group.runs.through.objects.get(run=run.id).id, run.id],
        ]


class TestGetAreObjectsDifferentiated(TestCase):
    @staticmethod
    def test_get_are_objects_differentiated_on_change():
        objectgroup = factories.ObjectGroupFactory()
        factories.ObjectFactory(group=objectgroup)
        admin = ObjectGroupAdmin(ObjectGroup, admin_site=AdminSite())
        data = {}
        request = RequestFactory().post(
            reverse(CHANGE_VIEWNAME, args=[objectgroup.id]), data=data
        )

        assert admin.get_are_objects_differentiated(request, objectgroup)

    @staticmethod
    def test_get_are_objects_differentiated_on_post():
        objectgroup = ObjectGroup(id=1)
        admin = ObjectGroupAdmin(ObjectGroup, admin_site=AdminSite())
        request_with_differentiated_objects = RequestFactory().post(
            reverse(CHANGE_VIEWNAME, args=[objectgroup.id]),
            data={"object_set-TOTAL_FORMS": "12"},
        )
        request_without_differentiated_objects = RequestFactory().post(
            reverse(CHANGE_VIEWNAME, args=[objectgroup.id]),
            data={"object_set-TOTAL_FORMS": "0"},
        )

        assert admin.get_are_objects_differentiated(request_with_differentiated_objects)
        assert not admin.get_are_objects_differentiated(
            request_without_differentiated_objects
        )

    @staticmethod
    def test_get_are_objects_differentiated_on_get():
        objectgroup = ObjectGroup(id=1)
        admin = ObjectGroupAdmin(ObjectGroup, admin_site=AdminSite())
        request = RequestFactory().get(
            reverse(CHANGE_VIEWNAME, args=[objectgroup.id]),
        )
        assert not admin.get_are_objects_differentiated(request)


class TestObjectErosImport(TestCase):
    def setUp(self):
        self.admin = ObjectGroupAdmin(ObjectGroup, admin_site=AdminSite())

        self.run = factories.RunFactory(project=factories.ProjectWithLeaderFactory())
        self.member = self.run.project.members.first()
        self.object_group = factories.ObjectGroupFactory()

    def test_page_is_readonly_after_import(self):
        objectgroup = ObjectGroup(id=1, c2rmf_id="123")
        request = RequestFactory().get(reverse(CHANGE_VIEWNAME, args=[objectgroup.id]))
        request.user = self.member
        assert not self.admin.has_change_permission(request, objectgroup)

    def test_correct_form_class_is_used_after_import(self):
        objectgroup = ObjectGroup(id=1, c2rmf_id="123")
        request = RequestFactory().get(reverse(CHANGE_VIEWNAME, args=[objectgroup.id]))
        request.user = self.member
        assert (
            self.admin.get_form(request, objectgroup, change=True)
            == ObjectGroupImportC2RMFReadonlyForm
        )

    def test_fetch_object_from_eros_when_imported(self):
        objectgroup = factories.ObjectGroupFactory(c2rmf_id="123")
        request = RequestFactory().get(reverse(CHANGE_VIEWNAME, args=[objectgroup.id]))
        with mock.patch(
            "lab.objects.admin.fetch_full_objectgroup_from_eros"
        ) as fetch_mock:
            self.admin.get_object(request, objectgroup.id)
            fetch_mock.assert_called_once_with(objectgroup.c2rmf_id, objectgroup)
