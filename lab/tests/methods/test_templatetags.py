# pylint: disable=redefined-outer-name
# pylint: disable=invalid-name
from unittest.mock import patch

import pytest
from django.contrib.admin.helpers import AdminForm
from django.contrib.admin.sites import AdminSite
from django.contrib.admin.utils import flatten_fieldsets
from django.contrib.auth.models import AnonymousUser
from django.test.client import RequestFactory
from django.urls import reverse

from lab.widgets import DisabledSelectWithHidden

from ...admin.run import RunAdmin
from ...methods.dto import method_model_to_dto
from ...models import Run
from ...templatetags.methods import (
    _get_adminfield_name,
    detector_fields,
    filters_field,
    method_fields,
    run_methods_repr,
)
from .. import factories


@pytest.fixture(scope="module", autouse=True)
def patch_disabledselectwithhidden_optgroups():
    with patch.object(
        DisabledSelectWithHidden, "optgroups", return_value=[]
    ) as _fixture:
        yield _fixture


@pytest.fixture(scope="module", autouse=True)
def adminform():
    # pylint: disable=line-too-long
    # Raincoat: pypi package: Django==4.1.2 path: django/contrib/admin/options.py element: ModelAdmin._changeform_view

    run = Run(id=1)
    run_admin = RunAdmin(model=Run, admin_site=AdminSite())
    request = RequestFactory().get(reverse("admin:lab_run_change", args=[str(run.id)]))
    request.user = AnonymousUser()

    fieldsets = run_admin.get_fieldsets(request, run)
    ModelForm = run_admin.get_form(  # pylint: disable=invalid-name
        request, run, change=True, fields=flatten_fieldsets(fieldsets)
    )
    initial = run_admin.get_changeform_initial_data(request)
    form = ModelForm(initial=initial)
    return AdminForm(
        form,
        list(fieldsets),
        {},
        readonly_fields=run_admin.get_readonly_fields(request, run),
        model_admin=run_admin,
    )


def test_method_fields_returns_all_methods_in_order(adminform):
    assert [admin_field.field.name for admin_field in method_fields(adminform)] == [
        f.name for f in Run.get_method_fields()
    ]


def test_method_fields_returns_the_same_at_second_instanciation(adminform):
    assert method_fields(adminform)
    assert [_get_adminfield_name(f) for f in method_fields(adminform)] == [
        _get_adminfield_name(f) for f in method_fields(adminform)
    ]


def test_PIXE_detector_fields_returns_corresponding_detector_fieldnames_in_order(
    adminform,
):
    assert [
        detector_admin_field.field.name
        for detector_admin_field in detector_fields(adminform, "method_PIXE")
    ] == [
        "detector_LE0",
        "detector_HE1",
        "detector_HE2",
        "detector_HE3",
        "detector_HE4",
    ]


def test_LE0_filters_fields_returns_corresponding_filter_fieldnames_in_order(adminform):
    assert (
        filters_field(adminform, "detector_LE0").field.name
        == "filters_for_detector_LE0"
    )


@pytest.mark.django_db
def test_run_methods_repr():
    run = factories.RunFactory(
        method_PIXE=True,
        detector_LE0=True,
        filters_for_detector_LE0="Helium",
    )

    assert run_methods_repr(run) == {"methods": method_model_to_dto(run)}
