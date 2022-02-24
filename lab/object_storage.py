from boto3.session import Session
from botocore.config import Config
from django.conf import settings

client = Session().client(
    service_name="s3",
    region_name=settings.S3_BUCKET_REGION_NAME,
    use_ssl=True,
    endpoint_url=settings.S3_ENDPOINT_URL,
    aws_access_key_id=settings.S3_ACCESS_KEY_ID,
    aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
    config=Config(signature_version="s3v4"),
)


def create_presigned_download_url(key: str):
    return client.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": settings.S3_BUCKET_NAME,
            "Key": key,
        },
        ExpiresIn=1800,
    )


def create_presigned_delete_url(key: str):
    return client.generate_presigned_url(
        "delete_object",
        Params={
            "Bucket": settings.S3_BUCKET_NAME,
            "Key": key,
        },
        ExpiresIn=1800,
    )
