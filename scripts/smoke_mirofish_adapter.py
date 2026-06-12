from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.simulation.mirofish_adapter import MiroFishCliAdapter


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke test the PR OS MiroFish adapter.")
    parser.add_argument("--require-real", action="store_true", help="Fail when MiroFish is unavailable or times out.")
    parser.add_argument("--timeout", type=int, default=None, help="Override MIROFISH_TIMEOUT_SECONDS for this smoke.")
    args = parser.parse_args()

    adapter = MiroFishCliAdapter(timeout_seconds=args.timeout)
    if not adapter.available():
        message = "MiroFish CLI unavailable. Set MIROFISH_COMMAND, e.g. uv --directory /opt/mirofish run mirofish."
        print(message)
        return 1 if args.require_real else 0

    payload = {
        "client_name": "Demo 新能源品牌",
        "project_name": "年轻人新能源 SUV 上市预热",
        "raw_brief": "预算50万，新能源SUV上市预热，目标年轻家庭和科技兴趣人群，平台优先小红书和抖音。",
        "brand": {"target_tags": ["新能源", "年轻家庭", "科技感", "城市生活"]},
        "product": {"product_name": "新能源 SUV"},
        "matches": [
            {"creator_id": "demo_001", "creator_name": "科技车主小周", "score": 86},
            {"creator_id": "demo_002", "creator_name": "周末家庭实验室", "score": 81},
        ],
        "narratives": [{"title": "从通勤焦虑到智能生活方式"}],
    }
    try:
        report = adapter.run(payload)
    except Exception as exc:
        print(f"MiroFish adapter failed: {type(exc).__name__}: {exc}")
        return 1 if args.require_real else 0

    print(
        "MiroFish adapter ok:",
        f"engine={report.engine}",
        f"nodes={len(report.nodes)}",
        f"edges={len(report.edges)}",
        f"timeline={len(report.timeline)}",
        f"artifacts={len(report.artifacts)}",
        f"provider={os.getenv('MIROFISH_LLM_PROVIDER') or os.getenv('LLM_PROVIDER') or 'default'}",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
