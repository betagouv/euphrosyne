import base64
import hashlib
import hmac
import json
from datetime import datetime, timedelta

import requests
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


def _get_presigned_url():
    # Generate your access key from the console
    ACCESS_KEY_ID = settings.S3_ACCESS_KEY_ID
    SECRET_ACCESS_KEY = settings.S3_SECRET_ACCESS_KEY

    # S3 Region
    REGION = settings.S3_BUCKET_REGION_NAME

    # Example for the demo
    now = datetime.utcnow()
    DATE = now.strftime("%Y%m%d")
    X_AMZ_DATE = now.strftime("%Y%m%dT%H%M%SZ")
    EXPIRATION = (now + timedelta(minutes=30)).strftime("%Y%m%dT%H%M%SZ")

    policy = {
        "expiration": EXPIRATION,
        "conditions": [
            {"bucket": settings.S3_BUCKET_NAME},
            ["starts-with", "$key", ""],
            {"acl": "public-read"},
            {
                "x-amz-credential": ACCESS_KEY_ID
                + "/"
                + DATE
                + "/"
                + REGION
                + "/s3/aws4_request"
            },
            {"x-amz-algorithm": "AWS4-HMAC-SHA256"},
            {"x-amz-date": X_AMZ_DATE},
            {"success_action_status": "204"},
        ],
    }

    stringToSign = base64.b64encode(bytes(json.dumps(policy), encoding="utf8"))
    print("Base64 encoded policy:", stringToSign.decode("utf-8"), end="\n\n")

    dateKey = hmac.new(
        bytes("AWS4" + SECRET_ACCESS_KEY, "utf-8"),
        bytes(DATE, "utf-8"),
        digestmod=hashlib.sha256,
    ).digest()
    dateRegionKey = hmac.new(
        dateKey, bytes(REGION, "utf-8"), digestmod=hashlib.sha256
    ).digest()
    dateRegionServiceKey = hmac.new(
        dateRegionKey, bytes("s3", "utf-8"), digestmod=hashlib.sha256
    ).digest()
    signinKey = hmac.new(
        dateRegionServiceKey, bytes("aws4_request", "utf-8"), digestmod=hashlib.sha256
    ).digest()
    signature = hmac.new(signinKey, stringToSign, digestmod=hashlib.sha256).digest()
    return "{}?X-Amz-Algorithm={}&X-Amz-Credential={}&X-Amz-Date={}&X-Amz-Expires={}&X-Amz-SignedHeaders={}&X-Amz-Signature={}".format(
        settings.S3_ENDPONT_URL,
        "AWS4-HMAC-SHA256",
        f"{settings.S3_ACCESS_KEY_ID}/{DATE}/{REGION}/s3/aws4_request",
        X_AMZ_DATE,
        1800,
        "host",
        signature.hex(),
    )


def upload_project_document(fileobj, project_id: int):
    client = _get_client()
    client.upload_fileobj(
        fileobj,
        settings.S3_BUCKET_NAME,
        f"projects/{project_id}/documents/{fileobj.name}",
    )


def list_project_documents(project_id: int):
    url = _get_presigned_url()
    response = requests.get(url)

    client = _get_client()
    try:
        url = client.generate_presigned_url(
            ClientMethod="list_objects_v2",
            Params={
                "Bucket": settings.S3_BUCKET_NAME,
                # "Prefix": f"projects/{project_id}/documents/",
            },
        )
        # response = client.list_objects_v2(
        #     Bucket=settings.S3_BUCKET_NAME,
        #     Prefix=f"projects/{project_id}/documents/",
        # )
        # return response["Contents"]
    except ClientError as e:
        return []
    http_response = requests.get(url)
    return http_response
