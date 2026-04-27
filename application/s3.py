import boto3
from botocore.client import BaseClient
from botocore.config import Config

from application.settings import settings

__all__ = ["get_s3_client"]

_s3: BaseClient | None = None


def get_s3_client() -> BaseClient:
    global _s3

    if not _s3:
        _s3 = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url,
            aws_access_key_id=settings.s3_access_key_id,
            aws_secret_access_key=settings.s3_secret_access_key,
            region_name=settings.s3_region,
            config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
        )

    return _s3
