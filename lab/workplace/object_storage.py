from django.conf import settings

from lab.object_storage import client


def create_presigned_raw_data_upload_post(project_id: int, run_id: int):
    return client.generate_presigned_post(
        settings.S3_BUCKET_NAME,
        f"projects/{project_id}/runs/{run_id}/raw_data/${{filename}}",
        ExpiresIn=1800,
    )


def create_presigned_raw_data_list_url(project_id: int, run_id: int):
    return client.generate_presigned_url(
        "list_objects_v2",
        Params={
            "Bucket": settings.S3_BUCKET_NAME,
            "Prefix": f"projects/{project_id}/runs/{run_id}/raw_data/",
        },
        ExpiresIn=1800,
    )


def create_presigned_processed_data_upload_post(project_id: int, run_id: int):
    return client.generate_presigned_post(
        settings.S3_BUCKET_NAME,
        f"projects/{project_id}/runs/{run_id}/processed_data/${{filename}}",
        ExpiresIn=1800,
    )


def create_presigned_processed_data_list_url(project_id: int, run_id: int):
    return client.generate_presigned_url(
        "list_objects_v2",
        Params={
            "Bucket": settings.S3_BUCKET_NAME,
            "Prefix": f"projects/{project_id}/runs/{run_id}/processed_data/",
        },
        ExpiresIn=1800,
    )
