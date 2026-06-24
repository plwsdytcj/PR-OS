from __future__ import annotations

from pathlib import Path

from src.knowledge.service import create_knowledge_document
from src.knowledge.storage import load_all_documents

SEED_TITLE = "王明 PR-OS 行业判准摘要"
SEED_PATH = Path(__file__).resolve().parents[2] / "data" / "knowledge" / "wangming_pr_os_judgment.md"


def ensure_pr_os_judgment_knowledge(db_path: Path) -> dict[str, str]:
    if not SEED_PATH.exists():
        return {"status": "skipped", "reason": "seed file missing"}
    existing = load_all_documents(db_path)
    if any(doc.title == SEED_TITLE for doc in existing):
        return {"status": "exists", "title": SEED_TITLE}
    content = SEED_PATH.read_text(encoding="utf-8")
    result = create_knowledge_document(
        db_path,
        title=SEED_TITLE,
        content=content,
        source_type="pr_os_judgment",
        source_ref=str(SEED_PATH),
        industry="公关传媒",
        tags=["PR-OS", "判准", "结算", "二段传播", "业务类型"],
        metadata={"seed": True, "author": "wangming"},
    )
    return {"status": "created", "document_id": result["document"]["document_id"], "title": SEED_TITLE}
