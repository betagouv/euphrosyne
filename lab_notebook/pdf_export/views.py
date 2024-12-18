import concurrent.futures
import tempfile
import typing
from io import BytesIO

import requests
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404
from slugify import slugify

from euphro_tools.download_urls import get_storage_info_for_project_images
from lab import models as lab_models
from lab.measuring_points.models import MeasuringPoint
from lab.methods.dto import method_model_to_dto
from lab.objects.models import RunObjetGroupImage, construct_image_url_from_path
from lab.permissions import is_lab_admin

from .pdf import MeasuringPoint as MeasuringPointMapping
from .pdf import NotebookImage, PointLocation, create_pdf


def _get_image_content(image_url: str):
    response = requests.get(image_url, timeout=10)
    response.raise_for_status()
    return BytesIO(response.content)


# pylint: disable=too-many-locals
def export_notebook_to_pdf_view(request: HttpRequest, run_id: str):
    run = get_object_or_404(lab_models.Run, pk=run_id)

    points_qs = (
        MeasuringPoint.objects.filter(run=run)
        .select_related("object_group", "standard")
        .order_by("name")
    )

    run_object_group_images = (
        RunObjetGroupImage.objects.filter(
            id__in=points_qs.filter(image__isnull=False)
            .values_list("image__run_object_group_image", flat=True)
            .distinct()
        )
        .prefetch_related("measuring_point_images")
        .select_related("run_object_group", "run_object_group__objectgroup")
        .all()
    )
    storage_info = get_storage_info_for_project_images(run.project.slug)
    images: list[NotebookImage] = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [
            executor.submit(
                _get_image_content,
                construct_image_url_from_path(
                    image.path, storage_info["base_url"], storage_info["token"]
                ),
            )
            for image in run_object_group_images
        ]
        concurrent.futures.wait(futures)
        images_content = [future.result() for future in futures]

    for image, content in zip(run_object_group_images, images_content):
        image_url = construct_image_url_from_path(
            image.path, storage_info["base_url"], storage_info["token"]
        )
        locations: list[tuple[str, PointLocation]] = []
        for name, location in image.measuring_point_images.values_list(
            "measuring_point__name", "point_location"
        ):
            if location:
                locations.append((name, typing.cast(PointLocation, location)))

        images.append(
            {
                "file_name": image.file_name,
                "url": image_url,
                "transform": image.transform,
                "point_locations": locations,
                "content": content,
                "object_group_label": image.run_object_group.objectgroup.label,
            }
        )

    measuring_points: list[MeasuringPointMapping] = [
        {
            "name": point.name,
            "comments": point.comments,
            "object_group": (
                {"label": point.object_group.label} if point.object_group else None
            ),
            "standard": (
                {"label": point.standard.standard.label}
                if hasattr(point, "standard")
                else None
            ),
        }
        for point in MeasuringPoint.objects.filter(run=run)
        .select_related("object_group", "standard")
        .order_by("name")
    ]

    if not (
        is_lab_admin(request.user)
        or run.project.members.filter(id=request.user.id).exists()
    ):
        return HttpResponse(status=403)
    with tempfile.NamedTemporaryFile(delete_on_close=False) as fp:
        create_pdf(
            path=fp.name,
            run={
                "label": run.label,
                "project": {"slug": run.project.slug, "name": run.project.name},
                "particle_type": run.particle_type,
                "energy_in_keV": run.energy_in_keV,
                "beamline": run.beamline,
                "run_notebook": {"comments": run.run_notebook.comments},
            },
            run_methods=method_model_to_dto(run),
            measuring_points=measuring_points,
            images=images,
        )
        fp.close()
        with open(fp.name, mode="rb") as f:
            response = HttpResponse(f.read(), content_type="application/pdf")
            response["Content-Disposition"] = (
                f"attachment; filename={slugify(run.label)}_{run.project.slug}.pdf"
            )
            return response
