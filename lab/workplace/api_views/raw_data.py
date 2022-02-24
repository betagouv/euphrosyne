from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from lab.object_storage import (
    create_presigned_delete_url,
    create_presigned_download_url,
)
from lab.permissions import is_lab_admin_required, project_membership_required

from ..object_storage import (
    create_presigned_raw_data_list_url,
    create_presigned_raw_data_upload_post,
)


@login_required
@project_membership_required
@require_http_methods(["POST"])
def presigned_raw_data_list_url_view(request, project_id: int, run_id: int):
    url = create_presigned_raw_data_list_url(project_id, run_id)
    data = {"url": url}
    return JsonResponse(data)


@login_required
@is_lab_admin_required
@require_http_methods(["POST"])
def presigned_raw_data_upload_url_view(request, project_id: int, run_id: int):
    url = create_presigned_raw_data_upload_post(project_id, run_id)
    data = {"url": url}
    return JsonResponse(data)


@login_required
@project_membership_required
@require_http_methods(["POST"])
def presigned_raw_data_download_url_view(request, project_id: int):
    key = request.GET.get("key", None)
    if not key:
        return JsonResponse(
            data={"message": "`key` missing from query params"}, status=400
        )
    if not key.startswith(f"projects/{project_id}/runs/"):
        return JsonResponse(
            data={"message": "`key` does not match with project ID"}, status=400
        )
    url = create_presigned_download_url(key)
    data = {"url": url}
    return JsonResponse(data)


@login_required
@is_lab_admin_required
@require_http_methods(["POST"])
def presigned_raw_data_delete_url_view(request, project_id: int):
    key = request.GET.get("key", None)
    if not key:
        return JsonResponse(
            data={"message": "`key` missing from query params"}, status=400
        )
    if not key.startswith(f"projects/{project_id}/runs/"):
        return JsonResponse(
            data={"message": "`key` does not match with project ID"}, status=400
        )
    url = create_presigned_delete_url(key)
    data = {"url": url}
    return JsonResponse(data)
