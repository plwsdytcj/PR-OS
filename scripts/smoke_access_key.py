from __future__ import annotations

from pathlib import Path
import sys

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import web.server as server


def main() -> None:
    previous = server.ACCESS_KEY
    try:
        client = TestClient(server.app)
        server.ACCESS_KEY = ""
        assert client.get("/api/status").status_code == 200
        assert client.get("/api/creators").status_code == 200

        server.ACCESS_KEY = "secret-smoke"
        status = client.get("/api/status")
        assert status.status_code == 200
        assert status.json()["auth_required"] is True
        assert client.get("/api/creators").status_code == 401
        assert client.get("/api/creators", headers={"X-Access-Key": "wrong"}).status_code == 401
        ok = client.get("/api/creators", headers={"X-Access-Key": "secret-smoke"})
        assert ok.status_code == 200
        print("OK access key optional/required modes")
    finally:
        server.ACCESS_KEY = previous


if __name__ == "__main__":
    main()
