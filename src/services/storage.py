"""MinIO/S3 object storage wrapper for resume PDFs and reports."""

from __future__ import annotations

from io import BytesIO

from minio import Minio

from src.config.settings import settings
from src.utils.logging import get_logger

logger = get_logger(__name__)


class ObjectStorage:
    """MinIO client wrapper for file upload/download."""

    def __init__(self) -> None:
        self._client: Minio | None = None

    def connect(self) -> None:
        """Initialize the MinIO client."""
        self._client = Minio(
            endpoint=settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )
        self._ensure_bucket()
        logger.info("Connected to MinIO", endpoint=settings.minio_endpoint)

    def _ensure_bucket(self) -> None:
        """Create the default bucket if it doesn't exist."""
        if self._client and not self._client.bucket_exists(settings.minio_bucket):
            self._client.make_bucket(settings.minio_bucket)
            logger.info(f"Created bucket: {settings.minio_bucket}")

    @property
    def client(self) -> Minio:
        if self._client is None:
            raise RuntimeError("ObjectStorage not connected. Call connect() first.")
        return self._client

    def upload_file(
        self,
        object_name: str,
        data: bytes,
        content_type: str = "application/pdf",
        bucket: str | None = None,
    ) -> str:
        """Upload a file and return the object path."""
        bucket = bucket or settings.minio_bucket
        self.client.put_object(
            bucket_name=bucket,
            object_name=object_name,
            data=BytesIO(data),
            length=len(data),
            content_type=content_type,
        )
        return f"{bucket}/{object_name}"

    def download_file(self, object_name: str, bucket: str | None = None) -> bytes:
        """Download a file and return its contents."""
        bucket = bucket or settings.minio_bucket
        response = self.client.get_object(bucket_name=bucket, object_name=object_name)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()

    def delete_file(self, object_name: str, bucket: str | None = None) -> None:
        """Delete a file from storage."""
        bucket = bucket or settings.minio_bucket
        self.client.remove_object(bucket_name=bucket, object_name=object_name)


# Singleton
storage = ObjectStorage()
