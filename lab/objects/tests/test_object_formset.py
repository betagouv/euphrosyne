import csv
import io
from typing import Collection
from unittest.mock import MagicMock, patch

from django.contrib.admin.sites import AdminSite
from django.forms import ValidationError
from django.test import RequestFactory, TestCase
from django.urls import reverse

from lab.tests.factories import ObjectGroupFactory

from ..admin import CSVValidationError, ObjectFormSet, DifferentiatedObjectInline
from ..models import ObjectGroup, Period


class TestObjectFormset(TestCase):
    def setUp(self):
        self.inline = DifferentiatedObjectInline(ObjectGroup, admin_site=AdminSite())

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


class TestObjectFormsetWithTemplateUpload(TestCase):
    def setUp(self):
        self.inline = DifferentiatedObjectInline(ObjectGroup, admin_site=AdminSite())
        self.objectgroup = ObjectGroup(
            label="Object group",
            dating_period=Period.objects.get_or_create(label="XIXe")[0],
            materials=["wood"],
            object_count=0,
        )

    @staticmethod
    def create_request(data: dict):
        return RequestFactory().post(reverse("admin:lab_objectgroup_add"), data=data)

    @staticmethod
    def generate_csv_file(rows: Collection[dict[str, str]]):
        """Generate an valid in-memory file corresponding to the
        object template file."""
        file = io.StringIO()
        csv_writer = csv.DictWriter(file, ("label", "inventory", "collection"))
        csv_writer.writeheader()
        csv_writer.writerows(rows)
        file.seek(0)
        return io.BytesIO(bytes(file.read(), encoding="utf-8"))

    def test_object_creation_with_file_template(self):
        data = {
            "object_set-0-id": "",
            "object_set-0-label": "1",
            "object_set-0-inventory": "inventory",
            "object_set-0-collection": "collection",
            "object_set-0-group": "",
            "object_set-1-id": "",
            "object_set-1-group": "",
            "object_set-1-label": "2",
            "object_set-1-inventory": "inventory",
            "object_set-1-collection": "collection",
            "object_set-2-id": "",
            "object_set-2-group": "",
            "object_set-2-label": "3",
            "object_set-2-inventory": "inventory",
            "object_set-2-collection": "collection",
            "object_set-3-id": "",
            "object_set-3-group": "",
            "object_set-3-label": "4",
            "object_set-3-inventory": "inventory",
            "object_set-3-collection": "collection",
            "object_set-__prefix__-id": "",
            "object_set-__prefix__-group": "",
            "object_set-__prefix__-label": "",
            "object_set-__prefix__-inventory": "",
            "object_set-__prefix__-collection": "",
            "object_set-TOTAL_FORMS": "4",
            "object_set-INITIAL_FORMS": "0",
        }
        objects_to_insert = (
            {"label": "Objet 1", "inventory": "ABC", "collection": "DEF"},
            {"label": "Objet 2", "inventory": "DGT", "collection": "GHI"},
            {"label": "Objet 3", "inventory": "ZDT", "collection": "OPS"},
        )

        file = self.generate_csv_file(objects_to_insert)
        request = self.create_request(data)
        formset: ObjectFormSet = self.inline.get_formset(request)(
            data=data,
            files={"objects-template": file},
            instance=self.objectgroup,
            prefix="object_set",
        )

        assert formset.is_valid()
        self.objectgroup.save()
        formset.save()
        assert self.objectgroup.object_count == 3
        assert self.objectgroup.object_set.count() == 3
        for object_to_insert in objects_to_insert:
            assert self.objectgroup.object_set.filter(**object_to_insert).exists()

    def test_formset_invalid_when_missing_property(self):
        data = {"object_set-TOTAL_FORMS": 3}
        objects_to_insert = (
            {"label": "Objet 1", "inventory": "ABC", "collection": "DEF"},
            {"label": "", "inventory": "DGT", "collection": "GHI"},
            {"label": "Objet 3", "inventory": "ZDT", "collection": "OPS"},
        )

        file = self.generate_csv_file(objects_to_insert)
        request = self.create_request(data)
        formset: ObjectFormSet = self.inline.get_formset(request)(
            data=data,
            files={"objects-template": file},
            instance=self.objectgroup,
            prefix="object_set",
        )

        assert not formset.is_valid()
        assert formset.errors[1]
        assert "label" in formset.errors[1]

    @patch(
        "lab.objects.csv_upload.csv.DictReader",
    )
    def test_formset_invalid_when_invalid_csv(self, dict_reader_mock):
        dict_reader_mock.return_value.__iter__ = MagicMock(
            side_effect=UnicodeDecodeError("utf-8", b"error", 0, 1, "reason")
        )
        data = {"object_set-TOTAL_FORMS": 3}
        file = self.generate_csv_file([])
        request = self.create_request(data)
        formset: ObjectFormSet = self.inline.get_formset(request)(
            data=data,
            files={"objects-template": file},
            instance=self.objectgroup,
            prefix="object_set",
        )

        non_form_errors = formset.non_form_errors()
        assert len(non_form_errors) == 1
        assert non_form_errors.data[0].code == "csv-not-valid"
        assert isinstance(non_form_errors.data[0], CSVValidationError)
        assert len(formset.csv_differentiation_errors()) == 1
