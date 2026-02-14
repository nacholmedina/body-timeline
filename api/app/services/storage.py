import os
import uuid
from abc import ABC, abstractmethod

from flask import current_app
from werkzeug.datastructures import FileStorage


class StorageAdapter(ABC):
    @abstractmethod
    def upload(self, file: FileStorage, folder: str = "") -> dict:
        """Upload file and return {"storage_key": str, "url": str | None}."""
        ...

    @abstractmethod
    def get_url(self, storage_key: str) -> str:
        """Return a public or signed URL for the given storage key."""
        ...

    @abstractmethod
    def delete(self, storage_key: str) -> bool:
        ...


class LocalStorageAdapter(StorageAdapter):
    def __init__(self, base_path: str):
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)

    def upload(self, file: FileStorage, folder: str = "") -> dict:
        ext = os.path.splitext(file.filename or "file")[1].lower()
        key = f"{folder}/{uuid.uuid4().hex}{ext}" if folder else f"{uuid.uuid4().hex}{ext}"
        full_path = os.path.join(self.base_path, key)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        file.save(full_path)
        return {"storage_key": key, "url": f"/uploads/{key}"}

    def get_url(self, storage_key: str) -> str:
        return f"/uploads/{storage_key}"

    def delete(self, storage_key: str) -> bool:
        full_path = os.path.join(self.base_path, storage_key)
        if os.path.exists(full_path):
            os.remove(full_path)
            return True
        return False


class S3StorageAdapter(StorageAdapter):
    def __init__(self):
        import boto3
        session_kwargs = {}
        endpoint_url = current_app.config.get("S3_ENDPOINT_URL")
        if endpoint_url:
            session_kwargs["endpoint_url"] = endpoint_url
        self.client = boto3.client(
            "s3",
            region_name=current_app.config["S3_REGION"],
            aws_access_key_id=current_app.config["S3_ACCESS_KEY"],
            aws_secret_access_key=current_app.config["S3_SECRET_KEY"],
            **session_kwargs,
        )
        self.bucket = current_app.config["S3_BUCKET"]

    def upload(self, file: FileStorage, folder: str = "") -> dict:
        ext = os.path.splitext(file.filename or "file")[1].lower()
        key = f"{folder}/{uuid.uuid4().hex}{ext}" if folder else f"{uuid.uuid4().hex}{ext}"
        self.client.upload_fileobj(
            file.stream,
            self.bucket,
            key,
            ExtraArgs={"ContentType": file.content_type or "application/octet-stream"},
        )
        return {"storage_key": key, "url": None}

    def get_url(self, storage_key: str) -> str:
        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": storage_key},
            ExpiresIn=3600,
        )

    def delete(self, storage_key: str) -> bool:
        self.client.delete_object(Bucket=self.bucket, Key=storage_key)
        return True


_storage: StorageAdapter | None = None


def get_storage() -> StorageAdapter:
    global _storage
    if _storage is None:
        backend = current_app.config.get("STORAGE_BACKEND", "local")
        if backend == "s3":
            _storage = S3StorageAdapter()
        else:
            base = os.path.join(
                current_app.root_path, "..", current_app.config.get("STORAGE_LOCAL_PATH", "uploads")
            )
            _storage = LocalStorageAdapter(base)
    return _storage


def reset_storage():
    global _storage
    _storage = None
