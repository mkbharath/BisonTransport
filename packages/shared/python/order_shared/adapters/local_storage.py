"""Local storage adapter using MinIO (S3-compatible)."""

import asyncio
import logging
from typing import Any

import boto3
from botocore.config import Config

from order_shared.adapters.base import StorageAdapter, StorageFile

logger = logging.getLogger(__name__)


class MinIOStorageAdapter(StorageAdapter):
    """Storage adapter backed by MinIO (local S3-compatible service)."""

    def __init__(
        self,
        endpoint_url: str,
        access_key: str = "minioadmin",
        secret_key: str = "minioadmin",
        region: str = "us-east-1",
    ) -> None:
        self._client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
            config=Config(signature_version="s3v4", retries={"max_attempts": 3}),
        )
        self._endpoint_url = endpoint_url

    async def upload_file(
        self,
        bucket: str,
        key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> StorageFile:
        def _upload() -> None:
            self._client.put_object(
                Bucket=bucket,
                Key=key,
                Body=data,
                ContentType=content_type,
            )

        await asyncio.to_thread(_upload)
        logger.info(f"Uploaded {key} to {bucket} ({len(data)} bytes)")
        return StorageFile(
            key=key,
            bucket=bucket,
            content_type=content_type,
            size_bytes=len(data),
        )

    async def download_file(self, bucket: str, key: str) -> bytes:
        def _download() -> bytes:
            response = self._client.get_object(Bucket=bucket, Key=key)
            return response["Body"].read()

        return await asyncio.to_thread(_download)

    async def get_presigned_url(
        self, bucket: str, key: str, expires_in: int = 900
    ) -> str:
        def _presign() -> str:
            return self._client.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket, "Key": key},
                ExpiresIn=expires_in,
            )

        return await asyncio.to_thread(_presign)

    async def file_exists(self, bucket: str, key: str) -> bool:
        def _exists() -> bool:
            try:
                self._client.head_object(Bucket=bucket, Key=key)
                return True
            except Exception:
                return False

        return await asyncio.to_thread(_exists)

    async def delete_file(self, bucket: str, key: str) -> None:
        def _delete() -> None:
            self._client.delete_object(Bucket=bucket, Key=key)

        await asyncio.to_thread(_delete)
        logger.info(f"Deleted {key} from {bucket}")
