from __future__ import annotations

from pathlib import Path
import sys

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from web.server import app


def main() -> None:
    client = TestClient(app)
    status = client.get("/api/settings/data-sources")
    assert status.status_code == 200
    items = status.json()["items"]
    ids = {item["id"] for item in items}
    assert {"excel", "mock_api", "oneapi", "glm", "mirofish"}.issubset(ids)
    mock = client.post("/api/settings/data-sources/test", json={"source_id": "mock_api", "platform": "小红书", "identifier": "demo"})
    assert mock.status_code == 200
    assert mock.json()["ok"] is True
    oneapi = client.post("/api/settings/data-sources/test", json={"source_id": "oneapi"})
    assert oneapi.status_code == 200
    assert "ok" in oneapi.json()
    unknown = client.post("/api/settings/data-sources/test", json={"source_id": "unknown"})
    assert unknown.status_code == 400
    print(f"OK data_sources={len(items)} mock={mock.json()['ok']}")


if __name__ == "__main__":
    main()
