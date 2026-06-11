from __future__ import annotations

import base64
import os
from pathlib import Path
import sys
from uuid import uuid4

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from web.server import app


TENANT = f"kol-intake-smoke-{uuid4().hex[:8]}"
ADMIN_EMAIL = "kol-intake-smoke@pr-ai-os.local"
ADMIN_PASSWORD = "kol-intake-smoke-password"
HEADERS = {"X-Tenant-ID": TENANT}
if os.getenv("PR_AI_OS_ACCESS_KEY"):
    HEADERS["X-Access-Key"] = os.getenv("PR_AI_OS_ACCESS_KEY", "")

PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII="
)


def main() -> None:
    client = TestClient(app)
    _ensure_auth(client)

    text = client.post(
        "/api/kol-intake",
        headers=HEADERS,
        data={
            "input_type": "text",
            "text": "\n".join(
                [
                    "达人：小红书美妆测评 KOL",
                    "平台：小红书",
                    "粉丝：12.3万",
                    "报价：18000",
                    "内容：真实测评、成分分析、新品种草",
                    "适合：新品预热、信任背书",
                    "风险：硬广比例需要控制",
                ]
            ),
        },
    )
    assert text.status_code == 200, text.text
    text_body = text.json()
    assert text_body["imported"] == 1
    assert text_body["tag_summary"][0]["tag_count"] >= 5
    assert text_body["graph_summary"]["nodes"] > 0

    csv_bytes = (
        "达人,平台,粉丝,报价,内容方向,达人标签,备注\n"
        "抖音科技车评,抖音,45万,68000,新能源车测评,科技感;短视频测评,适合智驾新品预热\n"
        "B站长视频拆解,B站,18万,42000,家庭安全长视频,专业背书;长视频解释,适合信任建立\n"
    ).encode("utf-8-sig")
    file_response = client.post(
        "/api/kol-intake",
        headers=HEADERS,
        data={"input_type": "file"},
        files={"file": ("kol-intake.csv", csv_bytes, "text/csv")},
    )
    assert file_response.status_code == 200, file_response.text
    file_body = file_response.json()
    assert file_body["imported"] == 2
    assert sum(item["tag_count"] for item in file_body["tag_summary"]) >= 8

    image_response = client.post(
        "/api/kol-intake",
        headers=HEADERS,
        data={
            "input_type": "image",
            "name": "图片识别生活方式 KOL",
            "text": "平台：小红书\n粉丝：8.8万\n内容：生活方式种草、真实体验\n适合：预热、种草",
        },
        files={"file": ("profile-screenshot.png", PNG_1X1, "image/png")},
    )
    assert image_response.status_code == 200, image_response.text
    image_body = image_response.json()
    assert image_body["imported"] == 1
    assert image_body["source"] == "image"
    assert image_body["source_object"]["key"]
    assert image_body["tag_summary"][0]["tag_count"] >= 4

    total_tags = sum(item["tag_count"] for item in text_body["tag_summary"] + file_body["tag_summary"] + image_body["tag_summary"])
    print(
        "OK kol_intake "
        f"text_tags={text_body['tag_summary'][0]['tag_count']} "
        f"file_imported={file_body['imported']} "
        f"image_tags={image_body['tag_summary'][0]['tag_count']} "
        f"total_tags={total_tags}"
    )


def _ensure_auth(client: TestClient) -> None:
    if "X-Access-Key" in HEADERS:
        return
    payload = {
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD,
        "name": "KOL Intake Smoke",
    }
    response = client.post("/api/auth/bootstrap-admin", headers=HEADERS, json=payload)
    if response.status_code == 200:
        return
    login = client.post("/api/auth/login", headers=HEADERS, json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert login.status_code == 200, login.text


if __name__ == "__main__":
    main()
