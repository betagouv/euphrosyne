# pylint: disable=protected-access
import datetime
import json
from unittest import mock

from django.contrib.admin.sites import AdminSite
from django.test.client import RequestFactory
from django.urls import reverse

from ...admin import run as run_admin
from ...models import Run


def test_run_admin_seriazlied_data():
    request = RequestFactory().post(
        reverse("admin:lab_run_add"),
    )
    request.LANGUAGE_CODE = "fr-fr"
    run = Run(
        id=42,
        label="42label",
        start_date=datetime.datetime(2022, 1, 1, 0, 0),
        end_date=datetime.datetime(2022, 2, 2, 0, 0),
        particle_type="Proton",
        energy_in_keV=1000,
        beamline="Microbeam",
    )
    assert run_admin.RunAdmin._serialized_data(request, run) == {
        "id": "42",
        "label": "42label",
        "start_date": "01 janvier 2022 00:00",
        "end_date": "02 février 2022 00:00",
        "particle_type": "Proton",
        "energy_in_keV": "1000",
        "beamline": "Microbeam",
    }


@mock.patch.object(run_admin, "TemplateResponse")
@mock.patch.object(
    run_admin.RunAdmin, "_serialized_data", mock.Mock(return_value={"42": "42"})
)
def test_run_admin_add_with_popup_var_returns_json_data(mocked_template_response):
    run = Run()
    request = RequestFactory().post(
        reverse("admin:lab_run_add"), data={"project_id": 1, "_popup": 1}
    )
    admin = run_admin.RunAdmin(Run, admin_site=AdminSite())

    admin.response_add(request, run)

    mocked_template_response.assert_called_with(
        request,
        "admin/run_popup_response.html",
        {"popup_response_data": json.dumps({"action": "add", "data": {"42": "42"}})},
    )


@mock.patch.object(run_admin, "TemplateResponse")
@mock.patch.object(
    run_admin.RunAdmin, "_serialized_data", mock.Mock(return_value={"42": "42"})
)
def test_run_admin_change_with_popup_var_returns_json_data(mocked_template_response):
    run = Run(id=11)
    request = RequestFactory().post(
        reverse("admin:lab_run_change", args=[11]), data={"project_id": 1, "_popup": 1}
    )
    admin = run_admin.RunAdmin(Run, admin_site=AdminSite())

    admin.response_change(request, run)

    mocked_template_response.assert_called_with(
        request,
        "admin/run_popup_response.html",
        {"popup_response_data": json.dumps({"action": "change", "data": {"42": "42"}})},
    )


@mock.patch.object(run_admin, "TemplateResponse")
@mock.patch.object(
    run_admin.RunAdmin, "_serialized_data", mock.Mock(return_value={"42": "42"})
)
def test_run_admin_delete_with_popup_var_returns_json_data(mocked_template_response):
    run = Run(id=11)
    request = RequestFactory().post(
        reverse("admin:lab_run_delete", args=[11]), data={"_popup": 1}
    )
    admin = run_admin.RunAdmin(Run, admin_site=AdminSite())

    admin.response_delete(request, str(run), 11)

    mocked_template_response.assert_called_with(
        request,
        "admin/run_popup_response.html",
        {"popup_response_data": json.dumps({"action": "delete", "id": 11})},
    )
