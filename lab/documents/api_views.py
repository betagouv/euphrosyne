from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods

from ..models import Project
from ..permissions import is_lab_admin
from .object_storage import create_presigned_document_upload_post


@login_required
@require_http_methods(["GET"])
def presigned_document_upload_url_view(request, project_id: int):
    project = get_object_or_404(Project, pk=project_id)
    if (
        not is_lab_admin(request.user)
        and not project.members.filter(id=request.user.id).exists()
    ):
        raise PermissionDenied()

    url = create_presigned_document_upload_post(project_id)
    data = {"url": url}

    return JsonResponse(data)
