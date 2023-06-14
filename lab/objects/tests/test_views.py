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
    def test_form_valid(self):
        run = factories.RunFactory()

        view = ObjectImportC2RMFView()
        data = {
            "c2rmf_id": "abc",
            "label": "Rodondendron",
            "object_count": 1,
            IS_POPUP_VAR: 1,
        }
        view.request = RequestFactory().post(
            reverse("admin:lab_objectgroup_c2rmfimport") + f"?run={run.id}", data
        )
        with mock.patch(
            "lab.objects.forms.fetch_partial_objectgroup_from_eros"
        ) as mock_fn:
            mock_fn.return_value = {
                "c2rmf_id": "abc",
                "label": "Rodondendron",
            }
            form = forms.ObjectGroupImportC2RMFForm(data=data)
            response = view.form_valid(form)

        assert view.object.id
        assert models.ObjectGroup.objects.get(c2rmf_id="abc", label="Rodondendron")
        assert isinstance(response, TemplateResponse)
        assert "popup_response_data" in response.context_data
        popup_response_data = json.loads(response.context_data["popup_response_data"])
        assert popup_response_data["action"] == "add"
        assert popup_response_data["obj"]
        assert json.dumps(popup_response_data["objectgroup_run_run_ids"]) == json.dumps(
            list(
                view.object.runs.through.objects.filter(
                    objectgroup=view.object.id
                ).values_list("id", "run_id")
            )
        )
