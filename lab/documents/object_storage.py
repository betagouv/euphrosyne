from boto3.session import Session
from botocore.config import Config
from django.conf import settings


def _get_client():
    session = Session()
    return session.client(
        service_name="s3",
        region_name=settings.S3_BUCKET_REGION_NAME,
        use_ssl=True,
        endpoint_url=settings.S3_ENDPONT_URL,
        aws_access_key_id=settings.S3_ACCESS_KEY_ID,
        aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
        config=Config(signature_version="s3v4"),
    )


def create_presigned_document_upload_post(project_id: int):
    client = _get_client()
    return client.generate_presigned_post(
        settings.S3_BUCKET_NAME,
        f"projects/{project_id}/documents/${{filename}}",
        ExpiresIn=1800,
    )


def create_presigned_document_list_url(project_id: int):
    client = _get_client()
    return client.generate_presigned_url(
        "list_objects_v2",
        Params={
            "Bucket": settings.S3_BUCKET_NAME,
            "Prefix": f"projects/{project_id}/documents/",
        },
        ExpiresIn=1800,
    )


def create_presigned_document_download_url(key: str):
    client = _get_client()
    return client.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": settings.S3_BUCKET_NAME,
            "Key": key,
        },
        ExpiresIn=1800,
    )


def create_presigned_document_delete_url(key: str):
    client = _get_client()
    return client.generate_presigned_url(
        "delete_object",
        Params={
            "Bucket": settings.S3_BUCKET_NAME,
            "Key": key,
        },
        ExpiresIn=1800,
    )
