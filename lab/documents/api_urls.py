from django.urls import path

from .api_views import (
    presigned_document_delete_url_view,
    presigned_document_download_url_view,
    presigned_document_list_url_view,
    presigned_document_upload_url_view,
)

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
    path(
        "project/<project_id>/documents/presigned_download_url",
        presigned_document_download_url_view,
        name="presigned_document_download_url",
    ),
    path(
        "project/<project_id>/documents/presigned_delete_url",
        presigned_document_delete_url_view,
        name="presigned_document_delete_url",
    ),
]
