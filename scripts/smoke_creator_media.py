from __future__ import annotations

import base64
import os
from pathlib import Path
import sys
from uuid import uuid4

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["GLM_API_KEY"] = ""

from web.server import app


TENANT = f"creator-media-smoke-{uuid4().hex[:8]}"
HEADERS = {"X-Tenant-ID": TENANT}
PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII="
)


def main() -> None:
    client = TestClient(app)
    sample = client.post("/api/import/sample", headers=HEADERS)
    assert sample.status_code == 200, sample.text
    creators = client.get("/api/creators", headers=HEADERS)
    assert creators.status_code == 200, creators.text
    creator = creators.json()["items"][0]

    upload = client.post(
        f"/api/creators/{creator['creator_id']}/media/analyze",
        headers=HEADERS,
        files={"file": ("profile-screenshot.png", PNG_1X1, "image/png")},
    )
    assert upload.status_code == 200, upload.text
    body = upload.json()
    assert body["stored_object"]["key"]
    assert body["analysis"]["confidence"] in {"low", "medium", "high"}
    assert isinstance(body["suggested_patch"], dict)
    assert body["creator"]["media_assets"]
    assert "image_upload" in body["creator"]["data_sources"]

    detail = client.get(f"/api/creators/{creator['creator_id']}", headers=HEADERS)
    assert detail.status_code == 200, detail.text
    assert detail.json()["creator"]["media_assets"]

    print(f"OK creator_media creator={creator['creator_id']} key={body['stored_object']['key']}")


if __name__ == "__main__":
    main()
