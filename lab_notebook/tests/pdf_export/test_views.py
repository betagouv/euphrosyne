from unittest import mock

import pytest
from django.test import RequestFactory
from django.urls import reverse
from django.utils import timezone
from slugify import slugify

from euphro_auth.tests import factories as auth_factories
from lab.measuring_points.models import MeasuringPoint, MeasuringPointImage
from lab.objects.models import RunObjectGroup, RunObjetGroupImage
from lab.tests import factories as lab_factories
from lab_notebook.pdf_export.views import export_notebook_to_pdf_view


@pytest.mark.django_db
def test_export_notebook_to_pdf_view__permission_denied():
    run = lab_factories.RunFactory()

    request = RequestFactory()
    request.user = auth_factories.StaffUserFactory()

    response = export_notebook_to_pdf_view(request, run.id)

    assert response.status_code == 403


@pytest.mark.django_db
@mock.patch("lab_notebook.pdf_export.views._get_image_content")
@mock.patch("lab_notebook.pdf_export.views.create_pdf")
def test_export_notebook_to_pdf_view__run_not_found(
    create_pdf_mock: mock.MagicMock, get_image_content_mock: mock.MagicMock
):
    get_image_content_mock.return_value = b"une image"

    request = RequestFactory()
    request.user = auth_factories.LabAdminUserFactory()  # type: ignore

    run = lab_factories.RunFactory()
    og = lab_factories.ObjectGroupFactory()

    rog = RunObjectGroup.objects.create(run=run, objectgroup=og)
    rogi = RunObjetGroupImage.objects.create(
        run_object_group=rog,
        path="path/image.png",
        transform={"width:": 100, "height": 100, "x": 0, "y": 0},
    )

    point = MeasuringPoint.objects.create(
        name="001", run=run, object_group=og, comments="comments"
    )
    MeasuringPointImage.objects.create(
        measuring_point=point,
        run_object_group_image=rogi,
        point_location={"width:": 55, "height": 55, "x": 2, "y": 3},
    )

    response = export_notebook_to_pdf_view(request, run.id)  # type: ignore

    assert response.headers["Content-Type"] == "application/pdf"
    assert response.headers["Content-Disposition"] == (
        f"attachment; filename={slugify(run.label)}_{run.project.slug}.pdf"
    )

    assert get_image_content_mock.call_count == 1
    assert "path/image.png" in get_image_content_mock.call_args[0][0]

    assert create_pdf_mock.call_count == 1
    assert create_pdf_mock.call_args[1]["path"]
    assert create_pdf_mock.call_args[1]["run"] == {
        "label": run.label,
        "project": {"slug": run.project.slug, "name": run.project.name},
        "particle_type": run.particle_type,
        "energy_in_keV": run.energy_in_keV,
        "beamline": run.beamline,
        "run_notebook": {"comments": run.run_notebook.comments},
    }
    assert "run_methods" in create_pdf_mock.call_args[1]
    assert create_pdf_mock.call_args[1]["measuring_points"] == [
        {
            "name": "001",
            "comments": "comments",
            "object_group": {"label": og.label},
            "standard": None,
        }
    ]
    assert create_pdf_mock.call_args[1]["images"] == [
        {
            "file_name": "image.png",
            "url": get_image_content_mock.call_args[0][0],
            "transform": {"width:": 100, "height": 100, "x": 0, "y": 0},
            "point_locations": [("001", {"width:": 55, "height": 55, "x": 2, "y": 3})],
            "content": b"une image",
            "object_group_label": og.label,
        }
    ]


@pytest.mark.django_db
def test_cgu_acceptance_view_get(client):
    user = auth_factories.StaffUserFactory()
    client.force_login(user)

    response = client.get(reverse("cgu_acceptance"))

    assert response.status_code == 200
    assert "euphro_auth/cgu_acceptance.html" in [t.name for t in response.templates]


@pytest.mark.django_db
def test_cgu_acceptance_view_post(client):
    user = auth_factories.StaffUserFactory()
    client.force_login(user)

    request_time = timezone.now()
    response = client.post(reverse("cgu_acceptance"))

    user.refresh_from_db()
    assert response.status_code == 302
    assert response.url == "/"
    assert user.cgu_accepted_at is not None
    assert request_time <= user.cgu_accepted_at <= timezone.now()
