from django.urls import path

from .api_views import (
    presigned_processed_data_delete_url_view,
    presigned_processed_data_download_url_view,
    presigned_processed_data_list_url_view,
    presigned_processed_data_upload_url_view,
    presigned_raw_data_delete_url_view,
    presigned_raw_data_download_url_view,
    presigned_raw_data_list_url_view,
    presigned_raw_data_upload_url_view,
)

urlpatterns = [
    path(
        "project/<project_id>/workplace/<run_id>/processed_data/presigned_post",
        presigned_processed_data_upload_url_view,
        name="presigned_processed_data_upload_url",
    ),
    path(
        "project/<project_id>/workplace/<run_id>/processed_data/presigned_list_url",
        presigned_processed_data_list_url_view,
        name="presigned_processed_data_list_url",
    ),
    path(
        "project/<project_id>/workplace/processed_data/presigned_download_url",
        presigned_processed_data_download_url_view,
        name="presigned_processed_data_download_url",
    ),
    path(
        "project/<project_id>/workplace/processed_data/presigned_delete_url",
        presigned_processed_data_delete_url_view,
        name="presigned_processed_data_delete_url",
    ),
    path(
        "project/<project_id>/workplace/<run_id>/raw_data/presigned_post",
        presigned_raw_data_upload_url_view,
        name="presigned_raw_data_upload_url",
    ),
    path(
        "project/<project_id>/workplace/<run_id>/raw_data/presigned_list_url",
        presigned_raw_data_list_url_view,
        name="presigned_raw_data_list_url",
    ),
    path(
        "project/<project_id>/workplace/raw_data/presigned_download_url",
        presigned_raw_data_download_url_view,
        name="presigned_raw_data_download_url",
    ),
    path(
        "project/<project_id>/workplace/raw_data/presigned_delete_url",
        presigned_raw_data_delete_url_view,
        name="presigned_raw_data_delete_url",
    ),
]
