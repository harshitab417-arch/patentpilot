"""
PatentPilot scoring helpers.

This module keeps the final recommendation and ranking logic in one place,
while delegating explainable similarity/risk calculations to
patent_evaluation.py.
"""

from __future__ import annotations

from typing import Any

from app.agents.patent_evaluation import calculate_similarity_score


def compute_patent_risk_score(
    similarity: float | None = None,
    target_match: float | None = None,
    disease_match: float | None = None,
    legal_status: str | None = None,
    has_target: bool | None = None,
    has_disease: bool | None = None,
    evidence: dict[str, Any] | None = None,
) -> float:
    """
    Backward-compatible wrapper.

    New code should call calculate_similarity_score / calculate_risk_level
    directly. This helper now prefers structured evidence when available.
    """
    if evidence is not None:
        return calculate_similarity_score(evidence)

    # Legacy fallback for older callers.
    evidence_payload = {
        "moleculeMatch": "High" if (similarity or 0.0) >= 0.75 else "Medium",
        "targetMatch": "High" if (target_match or 0.0) >= 0.5 else "Low",
        "indicationMatch": "High" if (disease_match or 0.0) >= 0.5 else "Low",
        "mechanismMatch": "Medium" if legal_status else "Low",
    }
    return calculate_similarity_score(evidence_payload)


def compute_patent_score(
    similarity: float | None = None,
    target_match: float | None = None,
    disease_match: float | None = None,
    legal_status: str | None = None,
    has_target: bool | None = None,
    has_disease: bool | None = None,
    evidence: dict[str, Any] | None = None,
) -> float:
    """Backward-compatible alias for compute_patent_risk_score."""
    return compute_patent_risk_score(
        similarity=similarity,
        target_match=target_match,
        disease_match=disease_match,
        legal_status=legal_status,
        has_target=has_target,
        has_disease=has_disease,
        evidence=evidence,
    )


def compute_confidence_label(
    similarity: float | None,
    target_match: float | None,
    disease_match: float | None,
    has_metadata: bool,
) -> str:
    """
    Assign a coarse confidence label.

    For backward compatibility only. New code should rely on the
    stage-1 LLM confidence field.
    """
    score = float(similarity or 0.0)
    if score > 0.7 and (
        (target_match or 0.0) > 0.5 or (disease_match or 0.0) > 0.5
    ) and has_metadata:
        return "High"
    if score >= 0.4 or has_metadata:
        return "Medium"
    return "Low"


def rank_patents(patents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Rank patents by final similarity, then risk, then confidence."""

    def _rank_key(patent: dict[str, Any]) -> tuple[float, float, float, float]:
        similarity = float(patent.get("similarity_score", 0.0))
        risk = float(patent.get("risk_score", patent.get("patent_score", 0.0)))
        confidence = patent.get("confidence_label", "Low")
        confidence_rank = {"High": 3.0, "Medium": 2.0, "Low": 1.0}.get(confidence, 1.0)
        target = float(patent.get("target_match", 0.0))
        disease = float(patent.get("disease_match", 0.0))
        return (similarity, risk, confidence_rank, max(target, disease))

    return sorted(patents, key=_rank_key, reverse=True)


def compute_overall_recommendation(
    patent_scores: list[float],
    evidence_sufficient: bool,
) -> tuple[str, str]:
    """
    Produce the top-level risk recommendation.

    Scores may be supplied as 0-1 or 0-100 values.
    """
    if not evidence_sufficient:
        return (
            "Requires Expert Review",
            "Insufficient evidence: fewer than 3 patents were found. "
            "Absence of matches does not guarantee freedom to operate.",
        )

    if not patent_scores:
        return (
            "Requires Expert Review",
            "No patents found. Cannot assess patentability risk "
            "without evidence.",
        )

    max_score = max(patent_scores)
    if max_score <= 1.0:
        max_score *= 100.0

    if max_score >= 85.0:
        return (
            "High Patent Risk",
            f"Maximum patent similarity score of {max_score:.0f} exceeds "
            "the high-risk threshold (85). At least one patent shows "
            "significant overlap with the submitted molecule.",
        )
    if max_score >= 60.0:
        return (
            "Requires Expert Review",
            f"Maximum patent similarity score of {max_score:.0f} falls in "
            "the review range (60-84). Professional patent review is "
            "recommended.",
        )
    return (
        "Low Patent Risk",
        f"Maximum patent similarity score of {max_score:.0f} is below "
        "the concern threshold (60). No significant patent overlaps "
        "detected, but this is not a legal opinion.",
    )
