"""
PatentPilot patent evaluation utilities.

Pure helpers for:
  - Normalizing LLM evidence levels
  - Calculating explainable similarity scores
  - Calculating rule-based risk levels
"""

from __future__ import annotations

from typing import Any

EVIDENCE_LEVELS: dict[str, int] = {
    "low": 1,
    "medium": 2,
    "high": 3,
}

EVIDENCE_WEIGHTS: dict[str, float] = {
    "moleculeMatch": 0.40,
    "targetMatch": 0.25,
    "indicationMatch": 0.20,
    "mechanismMatch": 0.15,
}

RISK_LEVEL_TO_SCORE: dict[str, int] = {
    "High": 90,
    "Medium": 70,
    "Low": 30,
}


def normalize_evidence_level(value: Any) -> str:
    """Return one of Low / Medium / High, defaulting to Low."""
    if not isinstance(value, str):
        return "Low"

    cleaned = value.strip().lower()
    return cleaned.capitalize() if cleaned in EVIDENCE_LEVELS else "Low"


def evidence_level_to_numeric(value: Any) -> int:
    """Convert Low / Medium / High into 1 / 2 / 3."""
    return EVIDENCE_LEVELS.get(normalize_evidence_level(value).lower(), 1)


def evidence_level_to_fraction(value: Any) -> float:
    """Map Low / Medium / High to 0.33 / 0.67 / 1.0 for compatibility fields."""
    return evidence_level_to_numeric(value) / 3.0


def calculate_similarity_score(evidence: dict[str, Any]) -> float:
    """
    Convert stage-1 evidence into a 0-100 similarity score.

    The score is a weighted average of the four evidence dimensions:
    molecule, target, indication, and mechanism.
    """
    weighted_total = 0.0
    weight_sum = 0.0

    for field, weight in EVIDENCE_WEIGHTS.items():
        level_value = evidence.get(field)
        level_score = evidence_level_to_numeric(level_value)
        weighted_total += level_score * weight
        weight_sum += weight

    if weight_sum <= 0:
        return 0.0

    average_level = weighted_total / weight_sum
    normalized = ((average_level - 1.0) / 2.0) * 100.0
    return round(max(0.0, min(normalized, 100.0)), 1)


def calculate_risk_level(
    similarity_score: float,
    evidence: dict[str, Any],
) -> str:
    """
    Convert similarity + evidence into a categorical risk level.

    Rules:
    - High Risk: similarity >= 85 OR high molecule overlap AND high indication overlap
    - Medium Risk: similarity between 60 and 84
    - Low Risk: similarity below 60
    """
    molecule_level = normalize_evidence_level(evidence.get("moleculeMatch"))
    indication_level = normalize_evidence_level(evidence.get("indicationMatch"))

    if similarity_score >= 85.0 or (
        molecule_level == "High" and indication_level == "High"
    ):
        return "High"
    if 60.0 <= similarity_score < 85.0:
        return "Medium"
    return "Low"


def calculate_risk_score(risk_level: str) -> int:
    """Return a numeric score for display/sorting based on risk level."""
    return RISK_LEVEL_TO_SCORE.get(risk_level, 70)


def build_evidence_summary(evidence: dict[str, Any]) -> str:
    """Create a concise human-readable explanation from the structured evidence."""
    reason = evidence.get("reason")
    factors = evidence.get("matchedFactors") or []

    summary_parts: list[str] = []
    if isinstance(reason, str) and reason.strip():
        summary_parts.append(reason.strip())

    if factors:
        normalized_factors = ", ".join(
            str(item).strip() for item in factors if str(item).strip()
        )
        if normalized_factors:
            summary_parts.append(f"Matched factors: {normalized_factors}.")

    return " ".join(summary_parts).strip()
