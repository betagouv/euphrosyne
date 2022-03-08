from django.contrib.admin.sites import AdminSite
from django.forms import ValidationError
from django.test import RequestFactory, TestCase
from django.urls import reverse

from lab.tests.factories import ObjectGroupFactory

from ..admin import ObjectFormSet, ObjectInline
from ..models import ObjectGroup


class TestObjectFormset(TestCase):
    def setUp(self):
        self.inline = ObjectInline(ObjectGroup, admin_site=AdminSite())

    def test_disables_collection_when_parent_instance_has_collection(self):
        objectgroup: ObjectGroup = ObjectGroupFactory(collection="abc")
        request = RequestFactory().get(
            reverse("admin:lab_objectgroup_change", args=[objectgroup.id])
        )
        formset: ObjectFormSet = self.inline.get_formset(request, objectgroup)(
            data={}, instance=objectgroup
        )
        assert all(
            form.fields["collection"].widget.attrs["disabled"] for form in formset
        )

    def test_does_not_disable_collection_when_parent_instance_has_no_collection(self):
        objectgroup: ObjectGroup = ObjectGroupFactory(collection="")
        request = RequestFactory().get(
            reverse("admin:lab_objectgroup_change", args=[objectgroup.id])
        )
        formset: ObjectFormSet = self.inline.get_formset(request, objectgroup)(
            data={}, instance=objectgroup
        )
        assert all(
            not form.fields["collection"].widget.attrs["disabled"] for form in formset
        )

    def test_disables_inventory_when_parent_instance_has_inventory(self):
        objectgroup: ObjectGroup = ObjectGroupFactory(inventory="abc")
        request = RequestFactory().get(
            reverse("admin:lab_objectgroup_change", args=[objectgroup.id])
        )
        formset: ObjectFormSet = self.inline.get_formset(request, objectgroup)(
            data={}, instance=objectgroup
        )
        assert all(
            form.fields["inventory"].widget.attrs["disabled"] for form in formset
        )

    def test_does_not_disable_collection_when_parent_instance_has_no_inventory(self):
        objectgroup: ObjectGroup = ObjectGroupFactory(inventory="")
        request = RequestFactory().get(
            reverse("admin:lab_objectgroup_change", args=[objectgroup.id])
        )
        formset: ObjectFormSet = self.inline.get_formset(request, objectgroup)(
            data={}, instance=objectgroup
        )
        assert all(
            not form.fields["inventory"].widget.attrs["disabled"] for form in formset
        )

    def test_updates_object_count_on_save(self):
        objectgroup: ObjectGroup = ObjectGroupFactory(object_count=0)
        data = {
            "object_set-TOTAL_FORMS": "2",
            "object_set-INITIAL_FORMS": "0",
            "object_set-MIN_NUM_FORMS": "0",
            "object_set-MAX_NUM_FORMS": "1000",
            "object_set-0-group": objectgroup.id,
            "object_set-0-label": "1",
            "object_set-0-inventory": "",
            "object_set-0-collection": "",
            "object_set-1-group": objectgroup.id,
            "object_set-1-label": "2",
            "object_set-1-inventory": "",
            "object_set-1-collection": "",
        }
        request = RequestFactory().post(
            reverse("admin:lab_objectgroup_change", args=[objectgroup.id]), data=data
        )

        formset: ObjectFormSet = self.inline.get_formset(request, objectgroup)(
            data=data, instance=objectgroup
        )
        formset.is_valid()
        formset.save(commit=True)

        objectgroup.refresh_from_db()
        assert objectgroup.object_count == objectgroup.object_set.count()

    def test_does_not_update_object_count_when_no_objects(self):
        objectgroup: ObjectGroup = ObjectGroupFactory(object_count=3)
        objectgroup.object_set.all().delete()
        data = {
            "object_set-TOTAL_FORMS": "0",
            "object_set-INITIAL_FORMS": "0",
            "object_set-MIN_NUM_FORMS": "0",
            "object_set-MAX_NUM_FORMS": "1000",
        }
        request = RequestFactory().post(
            reverse("admin:lab_objectgroup_change", args=[objectgroup.id]), data=data
        )

        formset: ObjectFormSet = self.inline.get_formset(request, objectgroup)(
            data=data, instance=objectgroup
        )
        formset.is_valid()
        formset.save(commit=True)

        objectgroup.refresh_from_db()
        assert objectgroup.object_count == 3

    def test_validation_fails_when_single_form(self):
        objectgroup: ObjectGroup = ObjectGroupFactory(object_count=3)
        objectgroup.object_set.all().delete()
        data = {
            "object_set-TOTAL_FORMS": "1",
            "object_set-INITIAL_FORMS": "0",
            "object_set-MIN_NUM_FORMS": "0",
            "object_set-MAX_NUM_FORMS": "1000",
            "object_set-0-group": objectgroup.id,
            "object_set-0-label": "1",
            "object_set-0-inventory": "",
            "object_set-0-collection": "",
        }
        request = RequestFactory().post(
            reverse("admin:lab_objectgroup_change", args=[objectgroup.id]), data=data
        )

        formset: ObjectFormSet = self.inline.get_formset(request, objectgroup)(
            data=data, instance=objectgroup
        )
        with self.assertRaises(ValidationError) as cxt_manager:
            formset.clean()
            assert cxt_manager.exception.code == "differentiated-object-group-too-few"
