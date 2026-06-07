from __future__ import annotations

from pathlib import Path
from typing import Any

from src.knowledge.chunking import chunk_text
from src.knowledge.embedding import cosine_similarity, embed_text, tokenize
from src.knowledge.schemas import KnowledgeChunk, KnowledgeDocument, chunk_id_for, document_id_for, now_iso
from src.knowledge.storage import count_knowledge, load_all_chunks, load_all_documents, load_chunks_for_document, upsert_chunk, upsert_document
from src.schemas import split_tags


def create_knowledge_document(
    db_path: Path,
    title: str,
    content: str,
    source_type: str = "manual",
    source_ref: str = "",
    client_id: str = "",
    project_id: str = "",
    industry: str = "",
    tags: list[str] | str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    title = title.strip() or "未命名知识"
    content = content.strip()
    if not content:
        raise ValueError("content is required")
    tag_list = split_tags(tags)
    document = KnowledgeDocument(
        document_id=document_id_for(title, content, source_type),
        title=title,
        source_type=source_type.strip() or "manual",
        source_ref=source_ref.strip(),
        client_id=client_id.strip(),
        project_id=project_id.strip(),
        industry=industry.strip(),
        tags=tag_list,
        metadata=metadata or {},
    )
    chunks = []
    for index, chunk_content in enumerate(chunk_text(content), start=1):
        chunk = KnowledgeChunk(
            chunk_id=chunk_id_for(document.document_id, index, chunk_content),
            document_id=document.document_id,
            chunk_index=index,
            title=document.title,
            content=chunk_content,
            embedding=embed_text(" ".join([document.title, chunk_content, *tag_list, document.industry])),
            token_estimate=max(1, len(chunk_content) // 2),
            source_type=document.source_type,
            client_id=document.client_id,
            project_id=document.project_id,
            industry=document.industry,
            tags=tag_list,
            metadata=document.metadata,
        )
        chunks.append(chunk)
    document.chunk_count = len(chunks)
    document.updated_at = now_iso()
    upsert_document(db_path, document)
    for chunk in chunks:
        upsert_chunk(db_path, chunk)
    return {"document": document.to_dict(), "chunks": [chunk.to_dict() for chunk in chunks]}


def list_knowledge_documents(db_path: Path) -> list[dict[str, Any]]:
    documents = load_all_documents(db_path)
    return [document.to_dict() for document in documents]


def knowledge_document_detail(db_path: Path, document_id: str) -> dict[str, Any] | None:
    docs = [document for document in load_all_documents(db_path) if document.document_id == document_id]
    if not docs:
        return None
    document = docs[0]
    chunks = load_chunks_for_document(db_path, document_id)
    return {"document": document.to_dict(), "chunks": [chunk.to_dict() for chunk in chunks]}


def search_knowledge_base(
    db_path: Path,
    query: str,
    top_k: int = 5,
    client_id: str = "",
    project_id: str = "",
    industry: str = "",
    source_type: str = "",
) -> list[dict[str, Any]]:
    query = query.strip()
    query_embedding = embed_text(query)
    query_tokens = set(tokenize(query))
    candidates = []
    for chunk in load_all_chunks(db_path):
        if client_id and chunk.client_id != client_id:
            continue
        if project_id and chunk.project_id != project_id:
            continue
        if industry and chunk.industry != industry:
            continue
        if source_type and chunk.source_type != source_type:
            continue
        vector_score = cosine_similarity(query_embedding, chunk.embedding)
        keyword_score = _keyword_score(query_tokens, chunk)
        score = round(vector_score * 0.7 + keyword_score * 0.3, 6)
        candidates.append(
            {
                "title": chunk.title,
                "source": "knowledge_base",
                "source_type": chunk.source_type,
                "content": chunk.content,
                "score": score,
                "vector_score": round(vector_score, 6),
                "keyword_score": round(keyword_score, 6),
                "ref_id": chunk.document_id,
                "chunk_id": chunk.chunk_id,
                "client_id": chunk.client_id,
                "project_id": chunk.project_id,
                "industry": chunk.industry,
                "tags": chunk.tags,
            }
        )
    candidates.sort(key=lambda item: item["score"], reverse=True)
    return candidates[: max(1, top_k)]


def knowledge_stats(db_path: Path) -> dict[str, Any]:
    counts = count_knowledge(db_path)
    documents = load_all_documents(db_path)
    source_counts: dict[str, int] = {}
    for document in documents:
        source_counts[document.source_type] = source_counts.get(document.source_type, 0) + 1
    return {"documents": counts["documents"], "chunks": counts["chunks"], "source_counts": source_counts}


def _keyword_score(query_tokens: set[str], chunk: KnowledgeChunk) -> float:
    if not query_tokens:
        return 0.0
    text_tokens = set(tokenize(" ".join([chunk.title, chunk.content, chunk.industry, *chunk.tags])))
    if not text_tokens:
        return 0.0
    return len(query_tokens & text_tokens) / max(1, len(query_tokens))
