import pytest
from django.contrib.admin.sites import AdminSite
from django.test.client import RequestFactory
from django.urls import reverse

from ...admin import run as run_admin
from ...models import Run
from ..factories import LabAdminUserFactory, RunFactory


@pytest.mark.django_db
def test_run_delete_popup_confirmation_shows_popup_input():
    run = RunFactory()
    request = RequestFactory().get(
        reverse("admin:lab_run_delete", args=[11]) + "?_popup=1"
    )
    user = LabAdminUserFactory()
    request.user = user
    admin = run_admin.RunAdmin(Run, admin_site=AdminSite())

    response = admin.changeform_view(request, object_id=str(run.id))

    assert '<input type="hidden" name="_popup" value="1">' in str(
        response.render().content
    )


@pytest.mark.django_db
def test_run_change_view_shows_popup_input():
    run = RunFactory()
    request = RequestFactory().get(
        reverse("admin:lab_run_change", args=[11]) + "?_popup=1"
    )
    user = LabAdminUserFactory()
    request.user = user
    admin = run_admin.RunAdmin(Run, admin_site=AdminSite())

    response = admin.changeform_view(request, object_id=str(run.id))

    assert (
        f'<a href="/admin/lab/run/{run.id}/delete/?_popup=1" class="deletelink">'
        in str(response.render().content)
    )
