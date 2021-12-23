from django.urls import path

from lab.documents.api_views import (
    presigned_document_list_url_view,
    presigned_document_upload_url_view,
)

app_name = "api"

urlpatterns = [
    path(
        "project/<project_id>/documents/presigned_post",
        presigned_document_upload_url_view,
        name="presigned_document_upload_url",
    ),
    path(
        "project/<project_id>/documents/presigned_list_url",
        presigned_document_list_url_view,
        name="presigned_document_list_url",
    ),
]
