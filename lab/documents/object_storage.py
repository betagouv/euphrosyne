from boto3.session import Session
from botocore.config import Config
from botocore.exceptions import ClientError
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


def upload_project_document(fileobj, project_id: int):
    client = _get_client()
    client.upload_fileobj(
        fileobj,
        settings.S3_BUCKET_NAME,
        f"projects/{project_id}/documents/{fileobj.name}",
    )


def list_project_documents(project_id: int):
    client = _get_client()
    try:
        response = client.list_objects_v2(
            Bucket=settings.S3_BUCKET_NAME, Prefix=f"projects/{project_id}/documents"
        )
        if "Contents" in response:
            documents = [obj["Key"].split("/")[-1] for obj in response["Contents"]]
            return documents
        return []
    except ClientError:
        return []
