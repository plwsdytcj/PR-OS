from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from src.kol_intelligence.schemas import KolEvidenceTag, KolGraphSnapshot, KolPrediction, evidence_tag_id, graph_snapshot_id, now_iso, prediction_id_for
from src.kol_intelligence.storage import (
    load_evidence_tag,
    load_evidence_tags,
    load_graph_snapshots,
    load_predictions,
    upsert_evidence_tag,
    upsert_graph_snapshot,
    upsert_prediction,
)
from src.schemas import CreatorProfile, split_tags
from src.storage.db import load_profile, load_profiles
from src.symbolic.creator_profiler import generate_creator_symbolic_profile
from src.symbolic.storage import load_creator_symbolic, upsert_creator_symbolic
from src.rules.storage import load_rule_config


CATEGORY_LABELS = {
    "industry": "行业适配",
    "content": "内容能力",
    "goal": "传播目标",
    "stage": "传播阶段",
    "budget": "预算适配",
    "risk": "风险",
    "platform": "平台",
    "symbolic": "符号资产",
    "persona": "人设/叙事",
    "case": "合作案例",
    "metric": "数据表现",
}

BRIEF_KEYWORDS = {
    "汽车": ["汽车", "车", "新能源", "suv", "智驾", "通勤", "露营"],
    "美妆护肤": ["美妆", "护肤", "成分", "抗老", "香氛"],
    "AI软件": ["ai", "大模型", "工具", "自动化", "效率", "agent"],
    "母婴": ["母婴", "宝宝", "亲子", "家庭"],
    "3C数码": ["手机", "电脑", "数码", "耳机", "相机"],
    "小红书": ["小红书", "种草", "笔记"],
    "抖音": ["抖音", "短视频", "直播"],
    "B站": ["b站", "bilibili", "长视频"],
    "预热": ["预热", "种草", "蓄水", "上市前"],
    "转化": ["转化", "卖货", "成交", "直播", "挂链"],
    "声量": ["声量", "曝光", "破圈", "出圈"],
    "信任": ["信任", "专业", "背书", "真实", "测评"],
    "年轻人": ["年轻", "genz", "z世代", "大学生", "新人群"],
}


def preview_creator_intelligence(db_path: Path, profile: CreatorProfile) -> dict[str, Any]:
    """Derive AI summary and evidence tags from a draft profile without persisting."""
    rule_config = load_rule_config(db_path)
    symbolic = generate_creator_symbolic_profile(profile, rule_config=rule_config)
    evidence_tags = [tag.to_dict() for tag in _derive_tags(profile, symbolic)]
    return {
        "evidence_tags": evidence_tags,
        "suggested_patch": _suggested_field_patch(profile, evidence_tags),
    }


def _suggested_field_patch(profile: CreatorProfile, evidence_tags: list[dict[str, Any]]) -> dict[str, Any]:
    field_map = {
        "industry": "industry_fit_tags",
        "content": "content_capability_tags",
        "goal": "suitable_goals",
        "risk": "risk_tags",
        "persona": "identity_tags",
        "case": "cooperation_brands",
        "stage": "suitable_stages",
        "budget": "budget_fit_tags",
    }
    existing: dict[str, list[str]] = {
        "industry_fit_tags": list(profile.industry_fit_tags),
        "content_capability_tags": list(profile.content_capability_tags),
        "suitable_goals": list(profile.suitable_goals),
        "risk_tags": list(profile.risk_tags),
        "identity_tags": list(profile.identity_tags),
        "cooperation_brands": list(profile.cooperation_brands),
        "suitable_stages": list(profile.suitable_stages),
        "budget_fit_tags": list(profile.budget_fit_tags),
    }
    patch: dict[str, Any] = {}
    if profile.ai_summary:
        patch["ai_summary"] = profile.ai_summary
    for item in evidence_tags:
        field = field_map.get(str(item.get("category") or ""))
        tag = str(item.get("tag") or "").strip()
        if not field or not tag:
            continue
        merged = list(existing.get(field, []))
        if tag not in merged:
            merged.append(tag)
            existing[field] = merged
            patch[field] = merged
    return patch


def analyze_creator_evidence_tags(db_path: Path, creator_id: str = "", limit: int = 200) -> dict[str, Any]:
    rule_config = load_rule_config(db_path)
    creators = [load_profile(db_path, creator_id)] if creator_id else load_profiles(db_path)[: max(1, limit)]
    creators = [creator for creator in creators if creator is not None]
    saved: list[KolEvidenceTag] = []
    for creator in creators:
        symbolic = load_creator_symbolic(db_path, creator.creator_id)
        if symbolic is None:
            symbolic = generate_creator_symbolic_profile(creator, rule_config=rule_config)
            upsert_creator_symbolic(db_path, symbolic)
        for tag in _derive_tags(creator, symbolic):
            upsert_evidence_tag(db_path, tag)
            saved.append(tag)
    snapshot = kol_intelligence_snapshot(db_path)
    return {"items": [item.to_dict() for item in saved], "snapshot": snapshot}


def kol_intelligence_snapshot(db_path: Path) -> dict[str, Any]:
    tags = load_evidence_tags(db_path)
    graphs = load_graph_snapshots(db_path)
    predictions = load_predictions(db_path)
    categories = Counter(tag.category for tag in tags)
    statuses = Counter(tag.status for tag in tags)
    creator_ids = {tag.creator_id for tag in tags}
    top_tags = Counter(tag.tag for tag in tags).most_common(16)
    return {
        "metrics": {
            "creators_with_tags": len(creator_ids),
            "evidence_tags": len(tags),
            "suggested_tags": statuses.get("suggested", 0),
            "confirmed_tags": statuses.get("confirmed", 0),
            "rejected_tags": statuses.get("rejected", 0),
            "graph_snapshots": len(graphs),
            "predictions": len(predictions),
            "categories": dict(categories),
            "statuses": dict(statuses),
        },
        "latest_graph": graphs[0].to_dict() if graphs else None,
        "latest_prediction": predictions[0].to_dict() if predictions else None,
        "top_tags": [{"tag": tag, "count": count} for tag, count in top_tags],
        "recent_tags": [tag.to_dict() for tag in tags[:80]],
    }


def list_creator_evidence_tags(db_path: Path, creator_id: str = "") -> list[dict[str, Any]]:
    return [tag.to_dict() for tag in load_evidence_tags(db_path, creator_id=creator_id)]


def evidence_review_queue(db_path: Path, status: str = "", creator_id: str = "", limit: int = 80) -> dict[str, Any]:
    tags = load_evidence_tags(db_path, creator_id=creator_id)
    if status:
        tags = [tag for tag in tags if tag.status == status]
    tags.sort(key=lambda tag: (_status_priority(tag.status), tag.category == "risk", tag.confidence, tag.score), reverse=True)
    return {
        "items": [tag.to_dict() for tag in tags[: max(1, limit)]],
        "metrics": {
            "total": len(tags),
            "suggested": sum(1 for tag in tags if tag.status == "suggested"),
            "confirmed": sum(1 for tag in tags if tag.status == "confirmed"),
            "rejected": sum(1 for tag in tags if tag.status == "rejected"),
        },
    }


def review_evidence_tag(db_path: Path, tag_id: str, payload: dict[str, Any], reviewer: str = "") -> KolEvidenceTag:
    tag = load_evidence_tag(db_path, tag_id)
    if tag is None:
        raise KeyError(tag_id)
    status = str(payload.get("status") or tag.status or "suggested").strip()
    if status not in {"suggested", "confirmed", "rejected", "needs_more_evidence"}:
        raise ValueError("invalid status")
    tag.status = status
    tag.reviewer_note = str(payload.get("reviewer_note") if payload.get("reviewer_note") is not None else tag.reviewer_note)
    tag.reviewed_by = reviewer or str(payload.get("reviewed_by") or tag.reviewed_by)
    tag.reviewed_at = now_iso()
    if "confidence" in payload:
        tag.confidence = _clamp_float(payload.get("confidence"), 0.0, 1.0, tag.confidence)
    if "score" in payload:
        tag.score = int(_clamp_float(payload.get("score"), 0, 100, tag.score))
    if "weight_delta" in payload:
        tag.weight_delta = int(_clamp_float(payload.get("weight_delta"), -50, 50, tag.weight_delta))
    if payload.get("evidence"):
        tag.evidence = list(dict.fromkeys([*tag.evidence, *split_tags(payload.get("evidence"))]))[:8]
    tag.version += 1
    tag.updated_at = now_iso()
    upsert_evidence_tag(db_path, tag)
    return tag


def bulk_review_evidence_tags(db_path: Path, payload: dict[str, Any], reviewer: str = "") -> dict[str, Any]:
    tag_ids = [str(item) for item in payload.get("tag_ids", []) if str(item).strip()]
    if not tag_ids:
        raise ValueError("tag_ids are required")
    updated = []
    patch = {key: value for key, value in payload.items() if key != "tag_ids"}
    for tag_id in tag_ids:
        try:
            updated.append(review_evidence_tag(db_path, tag_id, patch, reviewer=reviewer))
        except KeyError:
            continue
    return {"items": [tag.to_dict() for tag in updated], "updated": len(updated)}


def build_kol_knowledge_graph(db_path: Path, brief: str = "", creator_ids: list[str] | None = None, limit: int = 80) -> KolGraphSnapshot:
    rule_config = load_rule_config(db_path)
    category_labels = _category_labels(rule_config)
    tags = _usable_tags(load_evidence_tags(db_path))
    if not tags:
        analyze_creator_evidence_tags(db_path, limit=limit)
        tags = load_evidence_tags(db_path)
    if creator_ids:
        allowed = set(creator_ids)
        tags = [tag for tag in tags if tag.creator_id in allowed]
    creators = {creator.creator_id: creator for creator in load_profiles(db_path)}
    brief_terms = _brief_terms(brief, rule_config.get("brief_keywords"))
    creator_scores = _score_creators(tags, brief_terms)
    selected_ids = [creator_id for creator_id, _ in creator_scores.most_common(limit)] or list({tag.creator_id for tag in tags})[:limit]
    selected_tags = [tag for tag in tags if tag.creator_id in selected_ids]

    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, Any]] = []
    nodes["brief"] = {
        "id": "brief",
        "type": "brand",
        "label": "PR Brief" if brief else "KOL Intelligence",
        "stage": "input",
        "score": 100 if brief else 70,
        "detail": brief[:160],
    }

    for tag in selected_tags:
        creator = creators.get(tag.creator_id)
        creator_label = tag.creator_name or creator.name if creator else tag.creator_id
        creator_node_id = f"creator:{tag.creator_id}"
        category_node_id = f"category:{tag.category}"
        tag_node_id = f"tag:{tag.category}:{tag.tag}"
        nodes.setdefault(
            creator_node_id,
            {
                "id": creator_node_id,
                "type": "creator",
                "label": creator_label,
                "stage": "kol",
                "score": min(99, max(35, creator_scores.get(tag.creator_id, tag.score))),
                "detail": _creator_detail(creator),
            },
        )
        nodes.setdefault(
            category_node_id,
            {
                "id": category_node_id,
                "type": "product",
                "label": category_labels.get(tag.category, tag.category),
                "stage": "ontology",
                "score": 72,
            },
        )
        node_type = "risk-node" if tag.category == "risk" else "tag-node"
        nodes.setdefault(
            tag_node_id,
            {
                "id": tag_node_id,
                "type": node_type,
                "label": tag.tag,
                "stage": "tag",
                "score": tag.score,
                "confidence": tag.confidence,
                "detail": "；".join(tag.evidence[:2]),
            },
        )
        edges.append({"source": category_node_id, "target": tag_node_id, "label": "包含", "type": "ontology", "weight": 0.45})
        edges.append({"source": tag_node_id, "target": creator_node_id, "label": f"{int(tag.confidence * 100)}%", "type": "match", "weight": tag.confidence})
        if brief_terms and _tag_hits_brief(tag, brief_terms):
            edges.append({"source": "brief", "target": tag_node_id, "label": "激活", "type": "match", "weight": 0.85})
        elif brief:
            edges.append({"source": "brief", "target": category_node_id, "label": "推理", "type": "context", "weight": 0.3})

    evolution = _graph_evolution(selected_tags, creator_scores, brief_terms, category_labels)
    snapshot = KolGraphSnapshot(
        snapshot_id=graph_snapshot_id(brief, len(nodes)),
        brief=brief,
        nodes=list(nodes.values()),
        edges=_dedupe_edges(edges)[:240],
        evolution=evolution,
        stats={
            "creators": len({tag.creator_id for tag in selected_tags}),
            "tags": len({tag.tag for tag in selected_tags}),
            "evidence_edges": len(edges),
            "activated_terms": sorted(brief_terms)[:20],
        },
    )
    upsert_graph_snapshot(db_path, snapshot)
    return snapshot


def predict_kol_fit(db_path: Path, brief: str, top_n: int = 8) -> KolPrediction:
    if not brief.strip():
        raise ValueError("brief is required")
    rule_config = load_rule_config(db_path)
    category_labels = _category_labels(rule_config)
    tags = _usable_tags(load_evidence_tags(db_path))
    if not tags:
        analyze_creator_evidence_tags(db_path)
        tags = _usable_tags(load_evidence_tags(db_path))
    terms = _brief_terms(brief, rule_config.get("brief_keywords"))
    graph = build_kol_knowledge_graph(db_path, brief=brief, limit=max(30, top_n * 6))
    creators = {creator.creator_id: creator for creator in load_profiles(db_path)}
    grouped: dict[str, list[KolEvidenceTag]] = defaultdict(list)
    for tag in tags:
        grouped[tag.creator_id].append(tag)

    scored = []
    activated_tags = Counter()
    for creator_id, creator_tags in grouped.items():
        score, reasons, risks, path = _score_prediction(creator_tags, terms, category_labels)
        if score <= 0:
            continue
        creator = creators.get(creator_id)
        for reason in reasons:
            activated_tags[reason] += 1
        scored.append(
            {
                "creator_id": creator_id,
                "creator_name": creator.name if creator else creator_tags[0].creator_name,
                "platform": creator.platform if creator else "",
                "score": min(99, max(1, round(score))),
                "recommendation_level": _level(score),
                "reasons": reasons[:6],
                "risk_points": risks[:4],
                "path": path[:6],
                "evidence": _best_evidence(creator_tags, terms, category_labels),
            }
        )
    scored.sort(key=lambda item: item["score"], reverse=True)
    recommendations = scored[:top_n]
    prediction = KolPrediction(
        prediction_id=prediction_id_for(brief, top_n),
        brief=brief,
        recommendations=recommendations,
        activated_tags=[{"tag": tag, "count": count} for tag, count in activated_tags.most_common(12)],
        graph=graph.to_dict(),
        summary=_prediction_summary(recommendations, terms),
    )
    upsert_prediction(db_path, prediction)
    return prediction


def run_conversational_kol_graph(db_path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    brief = str(payload.get("message") or payload.get("brief") or "").strip()
    if not brief:
        raise ValueError("message is required")
    top_n = int(payload.get("top_n") or 8)
    client_name = str(payload.get("client_name") or "甲方").strip()
    project_name = str(payload.get("project_name") or "KOL Graph Run").strip()
    history = payload.get("history") if isinstance(payload.get("history"), list) else []
    history_text = "\n".join(str(item.get("content") or "") for item in history[-4:] if isinstance(item, dict))
    enriched_brief = "\n".join(item for item in [history_text, brief] if item).strip()

    if not load_evidence_tags(db_path):
        analyze_creator_evidence_tags(db_path)
    prediction = predict_kol_fit(db_path, enriched_brief, top_n=top_n)
    graph = prediction.graph or build_kol_knowledge_graph(db_path, brief=enriched_brief, limit=max(30, top_n * 6)).to_dict()
    frames = _conversation_graph_frames(graph, prediction.recommendations)
    steps = _conversation_steps(enriched_brief, prediction, frames)
    messages = [
        {"role": "user", "content": brief, "status": "completed"},
        {
            "role": "assistant",
            "content": f"我先把 {client_name} / {project_name} 的需求拆成 brief 节点、标签节点、候选 KOL 和风险节点。",
            "status": "thinking",
        },
        {
            "role": "assistant",
            "content": prediction.summary or "已完成 KOL 图谱推演。",
            "status": "completed",
        },
    ]
    return {
        "conversation_id": prediction.prediction_id,
        "status": "completed",
        "client_name": client_name,
        "project_name": project_name,
        "brief": enriched_brief,
        "messages": messages,
        "steps": steps,
        "graph_frames": frames,
        "graph": graph,
        "recommendations": prediction.recommendations,
        "activated_tags": prediction.activated_tags,
        "summary": prediction.summary,
        "prediction": prediction.to_dict(),
    }


def _derive_tags(creator: CreatorProfile, symbolic: Any) -> list[KolEvidenceTag]:
    items: list[tuple[str, str, float, int, str, list[str]]] = []

    def add(category: str, tag: str, confidence: float, score: int, source: str, evidence: list[str]) -> None:
        tag = str(tag or "").strip()
        if not tag:
            return
        items.append((category, tag, confidence, score, source, [item for item in evidence if item][:4]))

    for tag in creator.industry_fit_tags:
        add("industry", tag, 0.72, 68, "profile.industry_fit_tags", [creator.manual_notes, creator.bio])
    for tag in creator.content_capability_tags:
        add("content", tag, 0.74, 70, "profile.content_capability_tags", [creator.ai_summary, creator.manual_notes])
    for tag in creator.suitable_goals:
        add("goal", tag, 0.7, 66, "profile.suitable_goals", [creator.ai_summary, creator.manual_notes])
    for tag in creator.suitable_stages:
        add("stage", tag, 0.68, 62, "profile.suitable_stages", [creator.ai_summary, creator.manual_notes])
    for tag in creator.budget_fit_tags:
        add("budget", tag, 0.64, 58, "profile.budget_fit_tags", [f"报价 {creator.listed_price}" if creator.listed_price else "", creator.price_source])
    for tag in creator.risk_tags:
        add("risk", tag, 0.76, 72, "profile.risk_tags", [creator.manual_notes, creator.ai_summary])
    if creator.platform and creator.platform != "未知":
        add("platform", creator.platform, 0.9, 80, "profile.platform", [creator.homepage_url, creator.platform_user_id])
    if creator.cooperation_brands:
        for brand in creator.cooperation_brands[:8]:
            add("case", brand, 0.66, 60, "profile.cooperation_brands", creator.cooperation_formats[:3])
    if creator.engagement_rate:
        add("metric", "高互动" if creator.engagement_rate >= 0.03 else "互动需核验", 0.62, 64 if creator.engagement_rate >= 0.03 else 45, "profile.engagement_rate", [f"互动率 {creator.engagement_rate:.2%}"])
    if symbolic:
        for tag in getattr(symbolic, "primary_tags", []) + getattr(symbolic, "secondary_tags", []):
            add("symbolic", tag, max(0.58, float(getattr(symbolic, "confidence", 0.58) or 0.58)), 75, "symbolic.tags", _symbolic_evidence(symbolic))
        for tag in getattr(symbolic, "risk_tags", []):
            add("risk", tag, max(0.6, float(getattr(symbolic, "confidence", 0.6) or 0.6)), 78, "symbolic.risk_tags", _symbolic_evidence(symbolic))
        for value in [getattr(symbolic, "persona_structure", ""), getattr(symbolic, "narrative_style", ""), getattr(symbolic, "audience_fantasy", "")]:
            for tag in split_tags(value)[:3]:
                add("persona", tag, 0.6, 58, "symbolic.persona", _symbolic_evidence(symbolic))

    merged: dict[tuple[str, str], KolEvidenceTag] = {}
    for category, tag, confidence, score, source, evidence in items:
        key = (category, tag)
        existing = merged.get(key)
        if existing:
            existing.confidence = min(0.98, max(existing.confidence, confidence) + 0.03)
            existing.score = max(existing.score, score)
            existing.evidence = list(dict.fromkeys(existing.evidence + evidence))[:6]
            existing.source = f"{existing.source}, {source}"
            continue
        merged[key] = KolEvidenceTag(
            tag_id=evidence_tag_id(creator.creator_id, tag, category),
            creator_id=creator.creator_id,
            creator_name=creator.name,
            tag=tag,
            category=category,
            confidence=round(confidence, 3),
            score=score,
            source_type="derived",
            source=source,
            evidence=evidence or [creator.name],
        )
    return list(merged.values())


def _brief_terms(brief: str, brief_keywords: dict[str, Any] | None = None) -> set[str]:
    text = brief.lower()
    terms = set()
    keywords_map = brief_keywords if isinstance(brief_keywords, dict) and brief_keywords else BRIEF_KEYWORDS
    for canonical, keywords in keywords_map.items():
        if isinstance(keywords, str):
            keywords = [keywords]
        if any(str(keyword).lower() in text for keyword in keywords or []):
            terms.add(canonical)
    for token in re.findall(r"[\w\u4e00-\u9fff]{2,}", text):
        if len(token) <= 24:
            terms.add(token)
    return terms


def _score_creators(tags: list[KolEvidenceTag], terms: set[str]) -> Counter:
    scores: Counter = Counter()
    for tag in tags:
        base = _effective_score(tag) * tag.confidence
        if _tag_hits_brief(tag, terms):
            base *= 1.8
        if tag.category == "risk":
            base *= 0.35
        scores[tag.creator_id] += base
    return scores


def _score_prediction(tags: list[KolEvidenceTag], terms: set[str], category_labels: dict[str, str] | None = None) -> tuple[float, list[str], list[str], list[str]]:
    labels = category_labels or CATEGORY_LABELS
    score = 0.0
    reasons: list[str] = []
    risks: list[str] = []
    path: list[str] = []
    for tag in tags:
        hit = _tag_hits_brief(tag, terms)
        category_boost = 1.25 if tag.category in {"industry", "content", "goal", "symbolic", "platform"} else 1.0
        contribution = _effective_score(tag) * tag.confidence * category_boost
        if hit:
            contribution *= 2.1
            reasons.append(tag.tag)
            path.append(f"{labels.get(tag.category, tag.category)} -> {tag.tag} -> {tag.creator_name}")
        elif tag.category in {"content", "symbolic"}:
            contribution *= 0.45
        else:
            contribution *= 0.22
        if tag.category == "risk":
            risks.append(tag.tag)
            contribution *= 0.25
        score += contribution
    return math.sqrt(score) * 10, list(dict.fromkeys(reasons)), list(dict.fromkeys(risks)), list(dict.fromkeys(path))


def _tag_hits_brief(tag: KolEvidenceTag, terms: set[str]) -> bool:
    haystack = " ".join([tag.tag, tag.category, tag.source, *tag.evidence]).lower()
    return any(term.lower() in haystack for term in terms)


def _graph_evolution(tags: list[KolEvidenceTag], scores: Counter, terms: set[str], category_labels: dict[str, str] | None = None) -> list[dict[str, Any]]:
    labels = category_labels or CATEGORY_LABELS
    category_counts = Counter(tag.category for tag in tags)
    activated = [tag for tag in tags if _tag_hits_brief(tag, terms)]
    risks = [tag for tag in tags if tag.category == "risk"]
    top_creator = scores.most_common(1)[0][0] if scores else ""
    top_creator_name = next((tag.creator_name for tag in tags if tag.creator_id == top_creator), "")
    return [
        {"step": 1, "title": "接入达人数据", "detail": f"读取 {len({tag.creator_id for tag in tags})} 个达人，统一为证据标签。"},
        {"step": 2, "title": "形成标签本体", "detail": " / ".join(f"{labels.get(k, k)} {v}" for k, v in category_counts.most_common(5))},
        {"step": 3, "title": "Brief 激活路径", "detail": f"{len(activated)} 个标签被需求命中。"},
        {"step": 4, "title": "风险抑制", "detail": f"{len(risks)} 个风险标签参与降权和人工核验。"},
        {"step": 5, "title": "预测推荐", "detail": f"当前最强路径指向 {top_creator_name or top_creator or '待补充达人'}。"},
    ]


def _best_evidence(tags: list[KolEvidenceTag], terms: set[str], category_labels: dict[str, str] | None = None) -> list[str]:
    labels = category_labels or CATEGORY_LABELS
    ranked = sorted(tags, key=lambda tag: (_tag_hits_brief(tag, terms), tag.confidence, tag.score), reverse=True)
    evidence: list[str] = []
    for tag in ranked[:6]:
        evidence.append(f"{labels.get(tag.category, tag.category)}:{tag.tag} - {'；'.join(tag.evidence[:2])}")
    return evidence[:5]


def _category_labels(rule_config: dict[str, Any] | None = None) -> dict[str, str]:
    labels = (rule_config or {}).get("category_labels") if isinstance(rule_config, dict) else None
    if not isinstance(labels, dict):
        return CATEGORY_LABELS
    return {str(key): str(value) for key, value in labels.items() if str(key).strip() and str(value).strip()} or CATEGORY_LABELS


def _symbolic_evidence(symbolic: Any) -> list[str]:
    result = []
    for item in getattr(symbolic, "evidence", [])[:4]:
        if isinstance(item, dict):
            result.append(str(item.get("quote") or item.get("claim") or item))
        else:
            result.append(str(getattr(item, "quote", "") or getattr(item, "claim", "") or item))
    for value in [getattr(symbolic, "content_sample", ""), getattr(symbolic, "comment_sample", ""), getattr(symbolic, "case_sample", "")]:
        if value:
            result.append(str(value)[:180])
    return result[:4]


def _creator_detail(creator: CreatorProfile | None) -> str:
    if not creator:
        return ""
    parts = [creator.platform, f"粉丝 {creator.follower_count}" if creator.follower_count else "", f"报价 {creator.listed_price}" if creator.listed_price else ""]
    return " / ".join(part for part in parts if part)


def _dedupe_edges(edges: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    result = []
    for edge in edges:
        key = (edge.get("source"), edge.get("target"), edge.get("label"))
        if key in seen:
            continue
        seen.add(key)
        result.append(edge)
    return result


def _level(score: float) -> str:
    if score >= 84:
        return "强推荐"
    if score >= 68:
        return "推荐"
    if score >= 50:
        return "可测试"
    return "需人工判断"


def _prediction_summary(recommendations: list[dict[str, Any]], terms: set[str]) -> str:
    if not recommendations:
        return "当前 brief 没有命中足够强的 KOL 证据标签，建议补充达人内容样本或合作案例。"
    top = recommendations[0]
    terms_text = "、".join(sorted(terms)[:5]) or "当前需求"
    return f"{terms_text} 激活了 {len(recommendations)} 个候选达人；首推 {top['creator_name']}，分数 {top['score']}，主要依据：{'、'.join(top.get('reasons') or [])}。"


def _conversation_graph_frames(graph: dict[str, Any], recommendations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    nodes = graph.get("nodes") or []
    edges = graph.get("edges") or []
    recommendation_ids = {f"creator:{item.get('creator_id')}" for item in recommendations}
    frame_specs = [
        ("brief", "解析 Brief", {"input"}),
        ("ontology", "激活需求标签", {"input", "ontology", "tag"}),
        ("candidates", "拉入候选 KOL", {"input", "ontology", "tag", "kol"}),
        ("risk", "检查风险与证据", {"input", "ontology", "tag", "kol", "risk"}),
        ("final", "形成推荐名单", {"input", "ontology", "tag", "kol", "risk", "final"}),
    ]
    frames = []
    for frame_id, title, stages in frame_specs:
        frame_nodes = [
            node
            for node in nodes
            if node.get("stage") in stages
            or (frame_id == "risk" and node.get("type") == "risk-node")
            or (frame_id == "final" and node.get("id") in recommendation_ids)
        ]
        frame_node_ids = {node.get("id") for node in frame_nodes}
        frame_edges = [edge for edge in edges if edge.get("source") in frame_node_ids and edge.get("target") in frame_node_ids]
        frames.append(
            {
                "frame_id": frame_id,
                "title": title,
                "detail": _frame_detail(frame_id, graph, recommendations),
                "nodes": frame_nodes,
                "edges": frame_edges,
            }
        )
    return frames


def _conversation_steps(brief: str, prediction: KolPrediction, frames: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {"id": "brief", "label": "解析需求", "status": "done", "detail": brief[:120], "frame_id": "brief"},
        {
            "id": "tags",
            "label": "激活标签",
            "status": "done",
            "detail": "、".join(item.get("tag", "") for item in prediction.activated_tags[:6]),
            "frame_id": "ontology",
        },
        {
            "id": "graph",
            "label": "生成 KOL 图谱",
            "status": "done",
            "detail": f"{len((prediction.graph or {}).get('nodes') or [])} nodes / {len((prediction.graph or {}).get('edges') or [])} edges",
            "frame_id": "candidates",
        },
        {
            "id": "risk",
            "label": "风险与证据检查",
            "status": "done",
            "detail": f"{sum(len(item.get('risk_points') or []) for item in prediction.recommendations)} 个风险点进入判断",
            "frame_id": "risk",
        },
        {
            "id": "recommend",
            "label": "输出推荐名单",
            "status": "done",
            "detail": f"Top {len(prediction.recommendations)} KOL ready",
            "frame_id": "final",
        },
    ]


def _frame_detail(frame_id: str, graph: dict[str, Any], recommendations: list[dict[str, Any]]) -> str:
    stats = graph.get("stats") or {}
    if frame_id == "brief":
        return "把用户输入转成 PR Brief 节点，作为后续标签激活的起点。"
    if frame_id == "ontology":
        return f"激活 {len(stats.get('activated_terms') or [])} 个需求词，并连接到证据标签。"
    if frame_id == "candidates":
        return f"从证据标签反向拉入 {stats.get('creators', len(recommendations))} 个候选 KOL。"
    if frame_id == "risk":
        return "把风险标签和需要人工核验的路径显式暴露出来。"
    return f"输出 {len(recommendations)} 个可解释 KOL 推荐。"


def _status_priority(status: str) -> int:
    return {"suggested": 4, "needs_more_evidence": 3, "confirmed": 2, "rejected": 1}.get(status or "", 0)


def _usable_tags(tags: list[KolEvidenceTag]) -> list[KolEvidenceTag]:
    return [tag for tag in tags if tag.status != "rejected"]


def _effective_score(tag: KolEvidenceTag) -> float:
    multiplier = 1.15 if tag.status == "confirmed" else 0.72 if tag.status == "needs_more_evidence" else 1.0
    return max(1.0, min(100.0, (tag.score + tag.weight_delta) * multiplier))


def _clamp_float(value: Any, low: float, high: float, fallback: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return fallback
    return max(low, min(high, number))
