from __future__ import annotations

import re


def chunk_text(text: str, max_chars: int = 700, overlap: int = 120) -> list[str]:
    text = re.sub(r"\s+", " ", text.strip())
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + max_chars)
        window = text[start:end]
        split_at = _last_sentence_boundary(window)
        if split_at > max_chars * 0.45 and end < len(text):
            end = start + split_at
            window = text[start:end]
        chunks.append(window.strip())
        if end >= len(text):
            break
        start = max(0, end - overlap)
    return [chunk for chunk in chunks if chunk]


def _last_sentence_boundary(text: str) -> int:
    candidates = [text.rfind(mark) for mark in ["。", "！", "？", ".", "!", "?", "；", ";"]]
    return max(candidates) + 1 if max(candidates) >= 0 else -1
