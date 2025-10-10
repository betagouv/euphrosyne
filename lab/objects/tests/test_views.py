import json
from unittest import mock

from django.contrib.admin.options import IS_POPUP_VAR
from django.template.response import TemplateResponse
from django.test import RequestFactory, TestCase
from django.urls import reverse

from lab import models
from lab.tests import factories

from .. import forms
from ..views import ObjectImportErosView


class TestObjectImportC2RMFView(TestCase):
    def setUp(self):
        self.run = run = factories.RunFactory()
        self.view = ObjectImportErosView()
        self.url = reverse("admin:lab_objectgroup_erosimport") + f"?run={run.id}"

    def test_form_valid(self):
        data = {
            "provider_object_id": "abc",
            "label": "Rodondendron",
            IS_POPUP_VAR: 1,
        }
        self.view.request = RequestFactory().post(self.url, data)
        with mock.patch("lab.objects.forms.fetch_partial_objectgroup") as mock_fn:
            mock_fn.return_value = {
                "label": "Rodondendron",
            }
            form = forms.ObjectGroupImportErosForm(data=data)
            form.is_valid()  # Validate the form within the mock context
            response = self.view.form_valid(form)

        assert self.view.object.id
        assert models.ObjectGroup.objects.get(
            external_reference__provider_name="eros",
            external_reference__provider_object_id="ABC",
            label="Rodondendron",
        )
        assert isinstance(response, TemplateResponse)
        assert "popup_response_data" in response.context_data
        popup_response_data = json.loads(response.context_data["popup_response_data"])
        assert popup_response_data["action"] == "add"
        assert popup_response_data["obj"]
        assert json.dumps(popup_response_data["objectgroup_run_run_ids"]) == json.dumps(
            list(
                self.view.object.runs.through.objects.filter(
                    objectgroup=self.view.object.id
                ).values_list("id", "run_id")
            )
        )

    def test_form_valid_calls_invalid_if_run_relation_exists(self):
        object_reference = factories.ExternalObjectReferenceFactory(
            provider_name="eros", provider_object_id="F22299900"
        )
        object_reference.object_group.runs.add(self.run)

        data = {
            "provider_object_id": object_reference.provider_object_id,
            "label": "Rodondendron",
            "object_count": 1,
            IS_POPUP_VAR: 1,
        }
        self.view.request = RequestFactory().post(self.url, data)

        with mock.patch("lab.objects.forms.fetch_partial_objectgroup") as mock_fn:
            mock_fn.return_value = {
                "label": "Rodondendron",
            }
            form = forms.ObjectGroupImportErosForm(data=data)
            form.is_valid()  # Validate the form within the mock context

            with mock.patch.object(self.view, "form_invalid") as mock_method:
                self.view.form_valid(form)

                mock_method.assert_called()
                assert "__all__" in form.errors

    def test_form_valid_do_not_save_commit_if_objectgroup_exists(self):
        object_reference = factories.ExternalObjectReferenceFactory(
            provider_name="eros", provider_object_id="F2229990"
        )
        data = {
            "provider_object_id": object_reference.provider_object_id,
            "label": "Rodondendron",
            "object_count": 1,
            IS_POPUP_VAR: 1,
        }
        self.view.request = RequestFactory().post(self.url, data)
        with mock.patch("lab.objects.forms.fetch_partial_objectgroup") as mock_fn:
            mock_fn.return_value = {
                "label": "Rodondendron",
            }
            form = forms.ObjectGroupImportErosForm(data=data)
            form.instance = object_reference
            with mock.patch.object(form, "save") as save_fn_mock:
                save_fn_mock.return_value = object_reference
                self.view.form_valid(form)
                save_fn_mock.assert_called_once_with(commit=False)
