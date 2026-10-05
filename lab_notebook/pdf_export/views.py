import concurrent.futures
import tempfile
import typing
from io import BytesIO

from django import forms
from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404
from slugify import slugify

from euphro_tools.download_urls import get_storage_info_for_project_images
from euphro_tools.exceptions import EuphroToolsException
from lab import models as lab_models
from lab.measuring_points.models import MeasuringPoint
from lab.methods.dto import method_model_to_dto
from lab.objects.models import (
    RunObjetGroupImage,
    construct_image_url_from_path,
    get_image_provider_from_path,
)
from lab.objects.providers.pop import POP_IMAGE_URL
from lab.permissions import is_lab_admin
from shared.http import DownloadError, get_download_response

from .pdf import NotebookImage, PointLocation, create_pdf


def _get_image_content(
    image_url: str, provider: typing.Literal["azure", "eros", "pop"]
) -> BytesIO:
    """Download only from the trusted origins of this image's provider."""
    if provider == "azure":
        origins = settings.PDF_EXPORT_AZURE_IMAGE_ORIGINS
        if not image_url.lower().startswith("https://"):
            raise DownloadError("Azure images require HTTPS.")
    elif provider == "eros":
        origins = [settings.EROS_BASE_IMAGE_URL or settings.EUPHROSYNE_TOOLS_API_URL]
    else:
        origins = [POP_IMAGE_URL]
    response = get_download_response(image_url, allowed_origins=origins, timeout=10)
    try:
        return BytesIO(response.content)
    finally:
        response.close()


def _get_run_data(run: lab_models.Run):
    """Get run data including measuring points and images"""
    # Get all measuring points for the run
    measuring_points_qs = (
        MeasuringPoint.objects.filter(run=run)
        .select_related("object_group", "standard")
        .order_by("name")
    )

    # Get images related to measuring points
    run_object_group_images = (
        RunObjetGroupImage.objects.filter(
            id__in=measuring_points_qs.filter(image__isnull=False)
            .values_list("image__run_object_group_image", flat=True)
            .distinct()
        )
        .prefetch_related("measuring_point_images")
        .select_related("run_object_group", "run_object_group__objectgroup")
        .all()
    )

    # Get storage info for constructing image URLs
    storage_info = get_storage_info_for_project_images(run.project.slug)

    # Transform measuring points to the format expected by PDF generator
    measuring_points = [
        {
            "name": point.name,
            "comments": point.comments,
            "object_group": (
                {"label": point.object_group.label} if point.object_group else None
            ),
            "standard": (
                {"label": point.standard.standard.label}
                if hasattr(point, "standard") and point.standard
                else None
            ),
            "is_meaningful": point.is_meaningful,
        }
        for point in measuring_points_qs
    ]

    return run, run_object_group_images, storage_info, measuring_points


def _prepare_images(run_object_group_images, storage_info) -> list[NotebookImage]:
    """Prepare images with their content for PDF generation"""
    images: list[NotebookImage] = []

    # Fetch image content in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        image_urls = [
            construct_image_url_from_path(
                image.path, storage_info["base_url"], storage_info["token"]
            )
            for image in run_object_group_images
        ]

        futures = [
            executor.submit(
                _get_image_content, url, get_image_provider_from_path(image.path)
            )
            for url, image in zip(image_urls, run_object_group_images)
        ]
        concurrent.futures.wait(futures)
        images_content = [future.result() for future in futures]

    # Build image objects with their content
    for image, content, url in zip(run_object_group_images, images_content, image_urls):
        locations: list[tuple[str, PointLocation]] = []
        for name, location in image.measuring_point_images.values_list(
            "measuring_point__name", "point_location"
        ):
            if location:
                locations.append((name, typing.cast(PointLocation, location)))

        images.append(
            {
                "file_name": image.file_name,
                "url": url,
                "transform": image.transform,
                "point_locations": locations,
                "content": content,
                "object_group_label": image.run_object_group.objectgroup.label,
            }
        )

    return images


class ExportNotebookToPdfQueryParamsForm(forms.Form):
    skip_meaningless_points = forms.BooleanField(
        required=False,
    )


def export_notebook_to_pdf_view(request: HttpRequest, run_id: str) -> HttpResponse:
    """Generate and serve a PDF export of a run notebook"""
    run = get_object_or_404(lab_models.Run.objects.select_related("project"), pk=run_id)
    # Authorize before Tools API, image downloads or any other export work.
    if request.user.id is None or not (
        is_lab_admin(request.user)
        or run.project.members.filter(id=request.user.id).exists()
    ):
        return HttpResponse(status=403)

    # Parse query parameters
    query_params_form = ExportNotebookToPdfQueryParamsForm(request.GET)
    if not query_params_form.is_valid():
        return HttpResponse(status=400)

    try:
        run, run_object_group_images, storage_info, measuring_points = _get_run_data(
            run
        )
        images = _prepare_images(run_object_group_images, storage_info)
    except (DownloadError, EuphroToolsException):
        # Do not echo or log signed URLs or upstream exception messages.
        return HttpResponse(status=502)

    # Filter out meaningless points if requested
    skip_meaningless_points = query_params_form.cleaned_data.get(
        "skip_meaningless_points", False
    )
    if skip_meaningless_points:
        measuring_points = [
            point for point in measuring_points if point["is_meaningful"]
        ]

    # Generate PDF
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

        # Serve the generated PDF
        with open(fp.name, mode="rb") as f:
            response = HttpResponse(f.read(), content_type="application/pdf")
            response["Content-Disposition"] = (
                f"attachment; filename={slugify(run.label)}_{run.project.slug}.pdf"
            )
            return response
