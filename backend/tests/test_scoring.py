"""
Unit tests for the explainable patent evaluation pipeline.
"""

from __future__ import annotations

from app.agents.patent_evaluation import (
    calculate_risk_level,
    calculate_risk_score,
    calculate_similarity_score,
    normalize_evidence_level,
)
from app.agents.scoring import compute_overall_recommendation, rank_patents


def test_normalize_evidence_level_defaults_to_low() -> None:
    assert normalize_evidence_level("High") == "High"
    assert normalize_evidence_level("medium") == "Medium"
    assert normalize_evidence_level("unexpected") == "Low"


def test_similarity_score_uses_weighted_evidence_levels() -> None:
    evidence = {
        "moleculeMatch": "High",
        "targetMatch": "High",
        "indicationMatch": "Medium",
        "mechanismMatch": "Low",
    }

    score = calculate_similarity_score(evidence)

    assert score == 75.0


def test_risk_level_high_when_similarity_is_strong() -> None:
    evidence = {
        "moleculeMatch": "Medium",
        "targetMatch": "High",
        "indicationMatch": "High",
        "mechanismMatch": "Medium",
    }

    assert calculate_risk_level(88.0, evidence) == "High"


def test_risk_level_medium_and_low_thresholds() -> None:
    medium_evidence = {
        "moleculeMatch": "Medium",
        "targetMatch": "Medium",
        "indicationMatch": "Medium",
        "mechanismMatch": "Medium",
    }
    low_evidence = {
        "moleculeMatch": "Low",
        "targetMatch": "Low",
        "indicationMatch": "Low",
        "mechanismMatch": "Low",
    }

    assert calculate_risk_level(70.0, medium_evidence) == "Medium"
    assert calculate_risk_level(20.0, low_evidence) == "Low"


def test_risk_score_maps_risk_levels() -> None:
    assert calculate_risk_score("High") == 90
    assert calculate_risk_score("Medium") == 70
    assert calculate_risk_score("Low") == 30


def test_rank_patents_prefers_similarity_then_risk() -> None:
    patents = [
        {"patent_id": "B", "similarity_score": 72.0, "risk_score": 70, "confidence_label": "Medium"},
        {"patent_id": "A", "similarity_score": 88.0, "risk_score": 90, "confidence_label": "High"},
        {"patent_id": "C", "similarity_score": 55.0, "risk_score": 30, "confidence_label": "Low"},
    ]

    ranked = rank_patents(patents)

    assert [p["patent_id"] for p in ranked] == ["A", "B", "C"]


def test_overall_recommendation_uses_new_thresholds() -> None:
    rec, reasoning = compute_overall_recommendation([88.0, 74.0, 39.0], True)
    assert rec == "High Patent Risk"
    assert "88" in reasoning

    rec, _ = compute_overall_recommendation([74.0, 61.0], True)
    assert rec == "Requires Expert Review"

    rec, _ = compute_overall_recommendation([59.0, 20.0], True)
    assert rec == "Low Patent Risk"


def test_overall_recommendation_requires_evidence() -> None:
    rec, reasoning = compute_overall_recommendation([95.0], False)
    assert rec == "Requires Expert Review"
    assert "Insufficient evidence" in reasoning
