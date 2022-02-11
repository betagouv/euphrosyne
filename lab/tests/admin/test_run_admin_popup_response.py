# pylint: disable=protected-access
import json
from unittest import mock

from django.contrib.admin.sites import AdminSite
from django.template.response import TemplateResponse
from django.test.client import RequestFactory
from django.urls import reverse

from ...admin import run as run_admin
from ...models import Run


@mock.patch.object(run_admin.ModelAdmin, "response_add")
@mock.patch.object(run_admin, "convert_for_ui", mock.Mock(return_value={"42": "42"}))
def test_run_admin_add_with_popup_var_returns_json_data(mocked_response_add):
    run = Run()
    request = RequestFactory().post(
        reverse("admin:lab_run_add"), data={"project_id": 1, "_popup": 1}
    )
    admin = run_admin.RunAdmin(Run, admin_site=AdminSite())
    mocked_response_add.return_value = TemplateResponse(
        request,
        "some_template.html",
        {
            "popup_response_data": json.dumps(
                {"action": "add", "name": "some name", "obj": "some obj"}
            )
        },
    )

    response = admin.response_add(request, run)

    assert json.loads(response.context_data["popup_response_data"])["data"] == {
        "42": "42"
    }


@mock.patch.object(run_admin.ModelAdmin, "response_change")
@mock.patch.object(run_admin, "convert_for_ui", mock.Mock(return_value={"42": "42"}))
def test_run_admin_change_with_popup_var_returns_json_data(mocked_response_change):
    run = Run(id=11)
    request = RequestFactory().post(
        reverse("admin:lab_run_change", args=[11]), data={"project_id": 1, "_popup": 1}
    )
    admin = run_admin.RunAdmin(Run, admin_site=AdminSite())
    mocked_response_change.return_value = TemplateResponse(
        request,
        "some_template.html",
        {
            "popup_response_data": json.dumps(
                {
                    "action": "change",
                    "value": "some id",
                    "obj": "some obj",
                    "new_value": "some new id",
                }
            )
        },
    )

    response = admin.response_change(request, run)

    assert json.loads(response.context_data["popup_response_data"])["data"] == {
        "42": "42"
    }
