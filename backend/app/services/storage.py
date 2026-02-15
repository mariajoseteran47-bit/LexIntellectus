import io
from minio import Minio
from minio.error import S3Error
from datetime import timedelta
from app.core.config import settings

class StorageService:
    def __init__(self):
        self.client = Minio(
            settings.MINIO_ENDPOINT.replace("http://", "").replace("https://", ""),
            access_key=settings.MINIO_ROOT_USER,
            secret_key=settings.MINIO_ROOT_PASSWORD,
            secure=settings.MINIO_USE_SSL
        )
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        try:
            if not self.client.bucket_exists(settings.MINIO_BUCKET):
                self.client.make_bucket(settings.MINIO_BUCKET)
        except S3Error as e:
            print(f"Error checking/creating bucket: {e}")

    def upload_file(self, file_data: bytes, object_name: str, content_type: str) -> str:
        """Uploads a file and returns the object name."""
        try:
            self.client.put_object(
                settings.MINIO_BUCKET,
                object_name,
                io.BytesIO(file_data),
                len(file_data),
                content_type=content_type
            )
            return object_name
        except S3Error as e:
            raise Exception(f"Failed to upload file to MinIO: {e}")

    def get_presigned_url(self, object_name: str, expiration_minutes: int = 60) -> str:
        """Generates a presigned URL for downloading a file."""
        try:
            return self.client.get_presigned_url(
                "GET",
                settings.MINIO_BUCKET,
                object_name,
                expires=timedelta(minutes=expiration_minutes)
            )
        except S3Error as e:
            raise Exception(f"Failed to generate presigned URL: {e}")

    def delete_file(self, object_name: str):
        try:
            self.client.remove_object(settings.MINIO_BUCKET, object_name)
        except S3Error as e:
             # Log error but don't crash?
             print(f"Failed to delete file from MinIO: {e}")

storage_service = StorageService()
