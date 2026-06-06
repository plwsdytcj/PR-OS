from __future__ import annotations

import mimetypes
import os
import re
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
_SAFE_KEY_RE = re.compile(r"[^a-zA-Z0-9._/-]+")


@dataclass
class StoredObject:
    provider: str
    bucket: str
    key: str
    size: int
    content_type: str
    url: str = ""
    etag: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ObjectStore:
    provider = "base"

    def put_bytes(
        self,
        data: bytes,
        key: str,
        content_type: str = "application/octet-stream",
        metadata: dict[str, str] | None = None,
    ) -> StoredObject:
        raise NotImplementedError

    def status(self) -> dict[str, Any]:
        raise NotImplementedError


class LocalObjectStore(ObjectStore):
    provider = "local"

    def __init__(self, root: Path | None = None, public_base_url: str = "") -> None:
        self.root = root or Path(os.getenv("OBJECT_STORE_LOCAL_ROOT") or ROOT / "data" / "objects")
        self.public_base_url = public_base_url or os.getenv("OBJECT_STORE_PUBLIC_BASE_URL", "").rstrip("/")

    def put_bytes(
        self,
        data: bytes,
        key: str,
        content_type: str = "application/octet-stream",
        metadata: dict[str, str] | None = None,
    ) -> StoredObject:
        safe_key = sanitize_object_key(key)
        path = self.root / safe_key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        if metadata:
            meta_path = path.with_suffix(path.suffix + ".metadata.json")
            import json

            meta_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
        url = f"{self.public_base_url}/{safe_key}" if self.public_base_url else str(path)
        return StoredObject(
            provider=self.provider,
            bucket=str(self.root),
            key=safe_key,
            size=len(data),
            content_type=content_type,
            url=url,
        )

    def status(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "configured": True,
            "available": True,
            "bucket": str(self.root),
            "detail": "本地对象存储，用于开发和内部单机部署。",
        }


class S3CompatibleObjectStore(ObjectStore):
    provider = "s3"

    def __init__(
        self,
        bucket: str,
        endpoint_url: str = "",
        region_name: str = "",
        access_key_id: str = "",
        secret_access_key: str = "",
        public_base_url: str = "",
        provider: str = "s3",
    ) -> None:
        self.provider = provider
        self.bucket = bucket
        self.endpoint_url = endpoint_url
        self.region_name = region_name or "auto"
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key
        self.public_base_url = public_base_url.rstrip("/")

    def put_bytes(
        self,
        data: bytes,
        key: str,
        content_type: str = "application/octet-stream",
        metadata: dict[str, str] | None = None,
    ) -> StoredObject:
        if not self.bucket:
            raise RuntimeError("OBJECT_STORE_BUCKET is required")
        client = self._client()
        safe_key = sanitize_object_key(key)
        response = client.put_object(
            Bucket=self.bucket,
            Key=safe_key,
            Body=data,
            ContentType=content_type,
            Metadata=metadata or {},
        )
        url = f"{self.public_base_url}/{safe_key}" if self.public_base_url else ""
        return StoredObject(
            provider=self.provider,
            bucket=self.bucket,
            key=safe_key,
            size=len(data),
            content_type=content_type,
            url=url,
            etag=str(response.get("ETag") or "").strip('"'),
        )

    def status(self) -> dict[str, Any]:
        configured = bool(self.bucket and self.access_key_id and self.secret_access_key)
        return {
            "provider": self.provider,
            "configured": configured,
            "available": configured,
            "bucket": self.bucket,
            "endpoint_url": self.endpoint_url,
            "region": self.region_name,
            "detail": "S3-compatible 对象存储，可用于阿里云 OSS、Cloudflare R2、AWS S3 或 MinIO。",
        }

    def _client(self) -> Any:
        try:
            import boto3
        except ImportError as exc:
            raise RuntimeError("boto3 is required for S3-compatible object storage") from exc
        return boto3.client(
            "s3",
            endpoint_url=self.endpoint_url or None,
            region_name=self.region_name,
            aws_access_key_id=self.access_key_id or None,
            aws_secret_access_key=self.secret_access_key or None,
        )


def get_object_store() -> ObjectStore:
    provider = os.getenv("OBJECT_STORE_PROVIDER", "local").strip().lower() or "local"
    if provider == "local":
        return LocalObjectStore()
    if provider in {"s3", "oss", "r2", "minio"}:
        return S3CompatibleObjectStore(
            bucket=os.getenv("OBJECT_STORE_BUCKET", ""),
            endpoint_url=os.getenv("OBJECT_STORE_ENDPOINT_URL", ""),
            region_name=os.getenv("OBJECT_STORE_REGION", ""),
            access_key_id=os.getenv("OBJECT_STORE_ACCESS_KEY_ID", ""),
            secret_access_key=os.getenv("OBJECT_STORE_SECRET_ACCESS_KEY", ""),
            public_base_url=os.getenv("OBJECT_STORE_PUBLIC_BASE_URL", ""),
            provider=provider,
        )
    raise ValueError(f"unknown object store provider: {provider}")


def object_store_status() -> dict[str, Any]:
    try:
        store = get_object_store()
        return store.status()
    except Exception as exc:
        return {
            "provider": os.getenv("OBJECT_STORE_PROVIDER", "local"),
            "configured": False,
            "available": False,
            "detail": str(exc),
        }


def make_upload_key(tenant: str, filename: str, category: str = "uploads") -> str:
    suffix = Path(filename or "upload").suffix
    stem = Path(filename or "upload").stem or "upload"
    today = datetime.utcnow().strftime("%Y/%m/%d")
    return sanitize_object_key(f"{tenant}/{category}/{today}/{uuid.uuid4().hex[:12]}-{stem}{suffix}")


def guess_content_type(filename: str, fallback: str = "application/octet-stream") -> str:
    return mimetypes.guess_type(filename or "")[0] or fallback


def sanitize_object_key(value: str) -> str:
    key = _SAFE_KEY_RE.sub("-", str(value or "").replace("\\", "/")).strip("/.-")
    return key or f"upload-{uuid.uuid4().hex}"
