from __future__ import annotations

import sqlite3
from pathlib import Path

from src.knowledge.schemas import KnowledgeChunk, KnowledgeDocument
from src.storage.postgres_payload import fetch_payload, fetch_payloads, postgres_enabled, upsert_payload


def init_knowledge_db(path: Path) -> None:
    if postgres_enabled():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS knowledge_documents (
                document_id TEXT PRIMARY KEY,
                source_type TEXT NOT NULL,
                client_id TEXT NOT NULL DEFAULT '',
                project_id TEXT NOT NULL DEFAULT '',
                industry TEXT NOT NULL DEFAULT '',
                payload TEXT NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS knowledge_chunks (
                chunk_id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                source_type TEXT NOT NULL,
                client_id TEXT NOT NULL DEFAULT '',
                project_id TEXT NOT NULL DEFAULT '',
                industry TEXT NOT NULL DEFAULT '',
                payload TEXT NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def upsert_document(path: Path, document: KnowledgeDocument) -> None:
    if postgres_enabled():
        upsert_payload(
            path,
            "knowledge_documents",
            "document_id",
            document.document_id,
            document.to_json(),
            {
                "source_type": document.source_type,
                "client_id": document.client_id,
                "project_id": document.project_id,
                "industry": document.industry,
            },
        )
        return
    init_knowledge_db(path)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            INSERT INTO knowledge_documents (document_id, source_type, client_id, project_id, industry, payload, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(document_id) DO UPDATE SET
                source_type = excluded.source_type,
                client_id = excluded.client_id,
                project_id = excluded.project_id,
                industry = excluded.industry,
                payload = excluded.payload,
                updated_at = CURRENT_TIMESTAMP
            """,
            (document.document_id, document.source_type, document.client_id, document.project_id, document.industry, document.to_json()),
        )


def load_document(path: Path, document_id: str) -> KnowledgeDocument | None:
    if postgres_enabled():
        payload = fetch_payload(path, "knowledge_documents", "document_id", document_id)
        return KnowledgeDocument.from_json(payload) if payload else None
    init_knowledge_db(path)
    with sqlite3.connect(path) as conn:
        row = conn.execute("SELECT payload FROM knowledge_documents WHERE document_id = ?", (document_id,)).fetchone()
    return KnowledgeDocument.from_json(row[0]) if row else None


def load_all_documents(path: Path) -> list[KnowledgeDocument]:
    if postgres_enabled():
        return [KnowledgeDocument.from_json(payload) for payload in fetch_payloads(path, "knowledge_documents")]
    init_knowledge_db(path)
    with sqlite3.connect(path) as conn:
        rows = conn.execute("SELECT payload FROM knowledge_documents ORDER BY updated_at DESC").fetchall()
    return [KnowledgeDocument.from_json(row[0]) for row in rows]


def upsert_chunk(path: Path, chunk: KnowledgeChunk) -> None:
    if postgres_enabled():
        upsert_payload(
            path,
            "knowledge_chunks",
            "chunk_id",
            chunk.chunk_id,
            chunk.to_json(),
            {
                "document_id": chunk.document_id,
                "chunk_index": chunk.chunk_index,
                "source_type": chunk.source_type,
                "client_id": chunk.client_id,
                "project_id": chunk.project_id,
                "industry": chunk.industry,
            },
        )
        return
    init_knowledge_db(path)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            INSERT INTO knowledge_chunks (chunk_id, document_id, chunk_index, source_type, client_id, project_id, industry, payload, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(chunk_id) DO UPDATE SET
                document_id = excluded.document_id,
                chunk_index = excluded.chunk_index,
                source_type = excluded.source_type,
                client_id = excluded.client_id,
                project_id = excluded.project_id,
                industry = excluded.industry,
                payload = excluded.payload,
                updated_at = CURRENT_TIMESTAMP
            """,
            (chunk.chunk_id, chunk.document_id, chunk.chunk_index, chunk.source_type, chunk.client_id, chunk.project_id, chunk.industry, chunk.to_json()),
        )


def load_chunks_for_document(path: Path, document_id: str) -> list[KnowledgeChunk]:
    if postgres_enabled():
        return [KnowledgeChunk.from_json(payload) for payload in fetch_payloads(path, "knowledge_chunks", where="document_id = %s", params=(document_id,), order_by="chunk_index ASC")]
    init_knowledge_db(path)
    with sqlite3.connect(path) as conn:
        rows = conn.execute("SELECT payload FROM knowledge_chunks WHERE document_id = ? ORDER BY chunk_index ASC", (document_id,)).fetchall()
    return [KnowledgeChunk.from_json(row[0]) for row in rows]


def load_all_chunks(path: Path) -> list[KnowledgeChunk]:
    if postgres_enabled():
        return [KnowledgeChunk.from_json(payload) for payload in fetch_payloads(path, "knowledge_chunks")]
    init_knowledge_db(path)
    with sqlite3.connect(path) as conn:
        rows = conn.execute("SELECT payload FROM knowledge_chunks ORDER BY updated_at DESC").fetchall()
    return [KnowledgeChunk.from_json(row[0]) for row in rows]


def count_knowledge(path: Path) -> dict[str, int]:
    if postgres_enabled():
        return {"documents": len(load_all_documents(path)), "chunks": len(load_all_chunks(path))}
    init_knowledge_db(path)
    with sqlite3.connect(path) as conn:
        docs = conn.execute("SELECT COUNT(*) FROM knowledge_documents").fetchone()[0]
        chunks = conn.execute("SELECT COUNT(*) FROM knowledge_chunks").fetchone()[0]
    return {"documents": int(docs), "chunks": int(chunks)}
