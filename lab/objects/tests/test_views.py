import json
from unittest import mock

from django.contrib.admin.options import IS_POPUP_VAR
from django.template.response import TemplateResponse
from django.test import RequestFactory, TestCase
from django.urls import reverse

from lab import models
from lab.tests import factories

from .. import forms
from ..views import ObjectImportC2RMFView


class TestObjectImportC2RMFView(TestCase):
    def setUp(self):
        self.run = run = factories.RunFactory()
        self.view = ObjectImportC2RMFView()
        self.url = reverse("admin:lab_objectgroup_c2rmfimport") + f"?run={run.id}"

    def test_form_valid(self):
        data = {
            "c2rmf_id": "abc",
            "label": "Rodondendron",
            "object_count": 1,
            IS_POPUP_VAR: 1,
        }
        self.view.request = RequestFactory().post(self.url, data)
        with mock.patch(
            "lab.objects.forms.fetch_partial_objectgroup_from_eros"
        ) as mock_fn:
            mock_fn.return_value = {
                "c2rmf_id": "abc",
                "label": "Rodondendron",
            }
            form = forms.ObjectGroupImportC2RMFForm(data=data)
            response = self.view.form_valid(form)

        assert self.view.object.id
        assert models.ObjectGroup.objects.get(c2rmf_id="abc", label="Rodondendron")
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
        existing_obj = factories.ObjectGroupFactory(c2rmf_id="F22299900")
        existing_obj.runs.add(self.run)

        data = {
            "c2rmf_id": existing_obj.c2rmf_id,
            "label": "Rodondendron",
            "object_count": 1,
            IS_POPUP_VAR: 1,
        }
        self.view.request = RequestFactory().post(self.url, data)

        with mock.patch(
            "lab.objects.forms.fetch_partial_objectgroup_from_eros"
        ) as mock_fn:
            mock_fn.return_value = {
                "c2rmf_id": existing_obj.c2rmf_id,
                "label": "Rodondendron",
            }
            form = forms.ObjectGroupImportC2RMFForm(data=data)

            with mock.patch.object(self.view, "form_invalid") as mock_method:
                self.view.form_valid(form)

                mock_method.assert_called()
                assert "c2rmf_id" in form.errors

    def test_form_valid_do_not_save_commit_if_objectgroup_exists(self):
        existing_obj = factories.ObjectGroupFactory(c2rmf_id="F2229990")
        data = {
            "c2rmf_id": existing_obj.c2rmf_id,
            "label": "Rodondendron",
            "object_count": 1,
            IS_POPUP_VAR: 1,
        }
        self.view.request = RequestFactory().post(self.url, data)
        with mock.patch(
            "lab.objects.forms.fetch_partial_objectgroup_from_eros"
        ) as mock_fn:
            mock_fn.return_value = {
                "c2rmf_id": existing_obj.c2rmf_id,
                "label": "Rodondendron",
            }
            form = forms.ObjectGroupImportC2RMFForm(data=data)
            form.instance = existing_obj
            with mock.patch.object(form, "save") as save_fn_mock:
                save_fn_mock.return_value = existing_obj
                self.view.form_valid(form)
                save_fn_mock.assert_called_once_with(commit=False)
