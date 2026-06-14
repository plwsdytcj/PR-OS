from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.openclaw.adapter import OpenClawAdapter


def main() -> None:
    text = """Kolness OpenClaw Bridge 已完成本次 PR 任务。

## KOL 推荐
1. 贵州数码王（抖音）- score 81：行业标签匹配：汽车
2. 西南数码王（抖音）- score 81：行业标签匹配：汽车

## 主要风险
贵州数码王: 暂无明显风险。
"""
    names = OpenClawAdapter()._extract_kol_names(text)
    assert names == ["贵州数码王", "西南数码王"], names
    assert "Kolness OpenClaw Bridge" not in names
    print("OK openclaw_display names=clean")


if __name__ == "__main__":
    main()
