from __future__ import annotations

from io import BytesIO
from typing import BinaryIO

import pandas as pd

from src.normalize.mapper import FIELD_ALIASES


HEADER_KEYWORDS = {
    alias.replace(" ", "").replace("_", "").lower()
    for aliases in FIELD_ALIASES.values()
    for alias in aliases
}
EXTRA_HEADER_KEYWORDS = {
    "账号",
    "账号信息",
    "小红书昵称",
    "微信视频账号",
    "快手账号名称",
    "知乎账号",
    "粉丝数(万)",
    "粉丝量（w）",
    "粉丝（w）",
    "21-60s植入价",
    "定制视频",
    "报备图文（单品）",
    "蒲公英链接",
    "星图链接",
}
HEADER_KEYWORDS |= {item.replace(" ", "").replace("_", "").lower() for item in EXTRA_HEADER_KEYWORDS}


def load_table_file(file_obj: BinaryIO | BytesIO) -> dict[str, pd.DataFrame]:
    name = getattr(file_obj, "name", "")
    if name.lower().endswith(".csv"):
        return {"csv": pd.read_csv(file_obj)}
    raw_sheets = pd.read_excel(file_obj, sheet_name=None, header=None)
    parsed: dict[str, pd.DataFrame] = {}
    for sheet_name, raw_df in raw_sheets.items():
        df = normalize_messy_sheet(raw_df)
        if not df.empty:
            parsed[sheet_name] = df
    return parsed


def normalize_messy_sheet(raw_df: pd.DataFrame) -> pd.DataFrame:
    """Detect a likely header row in messy KOL rate-card sheets.

    Real media Excel files often have title rows, instruction rows, category rows,
    and only then the actual header. This function finds the row that most looks
    like a header and returns a dataframe with usable column names.
    """
    raw_df = raw_df.dropna(how="all").dropna(axis=1, how="all")
    if raw_df.empty:
        return pd.DataFrame()
    header_idx = detect_header_row(raw_df)
    if header_idx is None:
        return pd.DataFrame()
    header = [_clean_header(value, idx) for idx, value in enumerate(raw_df.iloc[header_idx].tolist())]
    data = raw_df.iloc[header_idx + 1 :].copy()
    data.columns = dedupe_headers(header)
    data = data.dropna(how="all")
    data = data.loc[:, [not str(col).startswith("__empty_") for col in data.columns]]
    return data.reset_index(drop=True)


def detect_header_row(raw_df: pd.DataFrame) -> int | None:
    best_idx: int | None = None
    best_score = 0
    for idx in range(min(len(raw_df), 25)):
        values = [str(value).strip() for value in raw_df.iloc[idx].tolist() if str(value).strip() and str(value).lower() != "nan"]
        if len(values) < 3:
            continue
        normalized = [_norm(value) for value in values]
        keyword_hits = sum(1 for value in normalized if value in HEADER_KEYWORDS or any(key in value for key in HEADER_KEYWORDS if len(key) >= 3))
        structural_hits = sum(1 for value in values if any(token in value for token in ["账号", "达人", "粉丝", "报价", "价格", "主页", "链接", "简介", "ID"]))
        score = keyword_hits * 2 + structural_hits + min(len(values), 12)
        if score > best_score:
            best_score = score
            best_idx = idx
    return best_idx if best_score >= 8 else None


def _clean_header(value: object, idx: int) -> str:
    text = str(value).strip()
    if not text or text.lower() == "nan":
        return f"__empty_{idx}"
    return " ".join(text.replace("\n", " ").split())


def _norm(value: str) -> str:
    return value.strip().replace(" ", "").replace("_", "").replace("\n", "").lower()


def dedupe_headers(headers: list[str]) -> list[str]:
    seen: dict[str, int] = {}
    result: list[str] = []
    for header in headers:
        count = seen.get(header, 0)
        seen[header] = count + 1
        result.append(header if count == 0 else f"{header}_{count + 1}")
    return result
