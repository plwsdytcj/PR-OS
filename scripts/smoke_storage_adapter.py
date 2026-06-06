from __future__ import annotations

import os
from pathlib import Path
import sys

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.storage.object_store import get_object_store, object_store_status
from web.server import app


TENANT = "storage-adapter-smoke"
HEADERS = {"X-Tenant-ID": TENANT}


def main() -> None:
    previous_provider = os.environ.get("OBJECT_STORE_PROVIDER")
    previous_root = os.environ.get("OBJECT_STORE_LOCAL_ROOT")
    local_root = ROOT / "data" / "objects" / "smoke"
    os.environ["OBJECT_STORE_PROVIDER"] = "local"
    os.environ["OBJECT_STORE_LOCAL_ROOT"] = str(local_root)
    try:
        status = object_store_status()
        assert status["provider"] == "local"
        assert status["available"] is True
        stored = get_object_store().put_bytes(b"hello", "smoke/test.txt", content_type="text/plain")
        assert stored.provider == "local"
        assert (local_root / "smoke" / "test.txt").read_bytes() == b"hello"

        client = TestClient(app)
        storage_response = client.get("/api/settings/storage", headers=HEADERS)
        assert storage_response.status_code == 200
        assert storage_response.json()["object_store"]["provider"] == "local"

        sample = ROOT / "data" / "raw" / "sample_creators.csv"
        with sample.open("rb") as handle:
            response = client.post(
                "/api/import/file",
                headers=HEADERS,
                files={"file": ("sample_creators.csv", handle, "text/csv")},
                data={"replace": "true", "all_sheets": "true"},
            )
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["imported"] > 0
        source = body["source_object"]
        assert source["provider"] == "local"
        assert source["key"].endswith("sample_creators.csv")
        assert (local_root / source["key"]).exists()
        print(f"OK storage_adapter provider={source['provider']} key={source['key']}")
    finally:
        if previous_provider is None:
            os.environ.pop("OBJECT_STORE_PROVIDER", None)
        else:
            os.environ["OBJECT_STORE_PROVIDER"] = previous_provider
        if previous_root is None:
            os.environ.pop("OBJECT_STORE_LOCAL_ROOT", None)
        else:
            os.environ["OBJECT_STORE_LOCAL_ROOT"] = previous_root


if __name__ == "__main__":
    main()
