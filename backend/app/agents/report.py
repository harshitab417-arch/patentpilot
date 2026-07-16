"""
PatentPilot Report Agent.

Assembles the final structured report from scored patents, AI analysis,
and the overall recommendation.
"""

import logging
from typing import Any

from app.services.gemini_service import GeminiService

logger = logging.getLogger(__name__)


async def generate_report(
    patents: list[dict[str, Any]],
    molecule_context: dict[str, Any],
    overall_recommendation: str,
    recommendation_reasoning: str,
    evidence_sufficient: bool,
    gemini_service: GeminiService | None = None,
) -> dict[str, Any]:
    """
    Generate a ``ReportData``-compatible dict.

    Args:
        patents: Scored and analysed patent list.
        molecule_context: Dict with keys smiles, target, disease.
        overall_recommendation: Top-level recommendation string.
        recommendation_reasoning: Human-readable reasoning.
        evidence_sufficient: Whether the evidence threshold was met.
        gemini_service: Injected GeminiService (or creates one).

    Returns:
        Dict with keys: executive_summary, key_patents,
        novelty_concerns, manual_review_list.
    """
    if gemini_service is None:
        gemini_service = GeminiService()

    # Build the analysis data payload for Gemini
    analysis_data: dict[str, Any] = {
        "canonical_smiles": molecule_context.get("smiles", ""),
        "target": molecule_context.get("target"),
        "disease": molecule_context.get("disease"),
        "overall_recommendation": overall_recommendation,
        "recommendation_reasoning": recommendation_reasoning,
        "evidence_sufficient": evidence_sufficient,
        "patents": patents,
    }

    # Call Gemini for the executive summary and novelty concerns
    try:
        gemini_report = await gemini_service.generate_report_summary(analysis_data)
    except Exception as exc:
        logger.error("Gemini report generation failed: %s", exc)
        gemini_report = {
            "executive_summary": (
                f"Patent analysis identified {len(patents)} relevant patent(s). "
                f"Recommendation: {overall_recommendation}. "
                f"{recommendation_reasoning}"
            ),
            "novelty_concerns": [],
            "manual_review_reasoning": recommendation_reasoning,
        }

    # Deterministic selections
    key_patents: list[str] = [
        p["patent_id"]
        for p in patents
        if p.get("risk_label") == "High" or p.get("similarity_score", 0) >= 85
    ]

    manual_review_list: list[str] = [
        p["patent_id"]
        for p in patents
        if p.get("confidence_label", "Low") in ("Low", "Medium")
    ]

    novelty_concerns: list[str] = gemini_report.get("novelty_concerns", [])
    if not novelty_concerns:
        # Derive from patent data when Gemini didn't provide any
        for p in patents:
            if p.get("similarity_score", 0) >= 85:
                novelty_concerns.append(
                    f"Patent {p['patent_id']} has a high similarity score of "
                    f"{p['similarity_score']:.0f}, indicating potential overlap."
                )

    report: dict[str, Any] = {
        "executive_summary": gemini_report.get("executive_summary", ""),
        "key_patents": key_patents,
        "novelty_concerns": novelty_concerns,
        "manual_review_list": manual_review_list,
    }

    logger.info(
        "Report generated: %d key patents, %d novelty concerns, "
        "%d patents for manual review.",
        len(key_patents),
        len(novelty_concerns),
        len(manual_review_list),
    )
    return report
