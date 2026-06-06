from __future__ import annotations

from pathlib import Path
import shutil
import sys

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.storage.db import save_profile
from src.schemas import CreatorProfile, stable_id
from web.server import TENANT_ROOT, app


def main() -> None:
    for tenant in ["smoke-alpha", "smoke-beta"]:
        path = TENANT_ROOT / tenant
        if path.exists():
            shutil.rmtree(path)
    client = TestClient(app)
    alpha_headers = {"X-Tenant-ID": "smoke-alpha"}
    beta_headers = {"X-Tenant-ID": "smoke-beta"}
    alpha_status = client.get("/api/status", headers=alpha_headers)
    assert alpha_status.status_code == 200
    assert alpha_status.json()["tenant"] == "smoke-alpha"
    assert alpha_status.headers["X-Tenant-ID"] == "smoke-alpha"

    from web.server import _tenant_paths

    alpha_db, _ = _tenant_paths("smoke-alpha")
    save_profile(
        alpha_db,
        CreatorProfile(
            creator_id=stable_id("smoke-alpha-creator"),
            name="Alpha 独立达人",
            platform="小红书",
            follower_count=10000,
            listed_price=8000,
            bio="tenant isolation smoke",
        ),
    )
    payload = {
        "client_name": "Alpha 客户",
        "project_name": "Alpha Campaign",
        "brief": "预算20万，新能源SUV预热，平台优先小红书。",
    }
    created = client.post("/api/platform/campaigns", json=payload, headers=alpha_headers)
    assert created.status_code == 200, created.text
    alpha_campaigns = client.get("/api/platform/campaigns", headers=alpha_headers).json()["items"]
    beta_campaigns = client.get("/api/platform/campaigns", headers=beta_headers).json()["items"]
    assert len(alpha_campaigns) == 1
    assert beta_campaigns == []
    assert "tenants/smoke-alpha" in alpha_status.json()["database"]
    print("OK tenant isolation alpha=1 beta=0")


if __name__ == "__main__":
    main()
