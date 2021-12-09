from functools import wraps

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from ..models import Project
from ..permissions import is_lab_admin
from .object_storage import (
    create_presigned_document_delete_url,
    create_presigned_document_download_url,
    create_presigned_document_list_url,
    create_presigned_document_upload_post,
)


def project_membership_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, project_id: int):
        try:
            project = Project.objects.get(pk=project_id)
        except Project.DoesNotExist:
            return JsonResponse(data={}, status=404)
        if (
            not is_lab_admin(request.user)
            and not project.members.filter(id=request.user.id).exists()
        ):
            return JsonResponse(data={}, status=403)
        return view_func(request, project_id)

    return _wrapped_view


@login_required
@project_membership_required
@require_http_methods(["POST"])
def presigned_document_list_url_view(request, project_id: int):
    url = create_presigned_document_list_url(project_id)
    data = {"url": url}
    return JsonResponse(data)


@login_required
@project_membership_required
@require_http_methods(["POST"])
def presigned_document_upload_url_view(request, project_id: int):
    url = create_presigned_document_upload_post(project_id)
    data = {"url": url}
    return JsonResponse(data)


@login_required
@project_membership_required
@require_http_methods(["POST"])
def presigned_document_download_url_view(request, project_id: int):
    key = request.GET.get("key", None)
    if not key:
        return JsonResponse(
            data={"message": "`key` missing from query params"}, status=400
        )
    if not key.startswith(f"projects/{project_id}/documents/"):
        return JsonResponse(
            data={"message": "`key` does not match with project ID"}, status=400
        )
    url = create_presigned_document_download_url(key)
    data = {"url": url}
    return JsonResponse(data)


@login_required
@project_membership_required
@require_http_methods(["POST"])
def presigned_document_delete_url_view(request, project_id: int):
    key = request.GET.get("key", None)
    if not key:
        return JsonResponse(
            data={"message": "`key` missing from query params"}, status=400
        )
    if not key.startswith(f"projects/{project_id}/documents/"):
        return JsonResponse(
            data={"message": "`key` does not match with project ID"}, status=400
        )
    url = create_presigned_document_delete_url(key)
    data = {"url": url}
    return JsonResponse(data)
