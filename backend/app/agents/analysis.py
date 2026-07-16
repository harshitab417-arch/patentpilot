"""
PatentPilot Analysis Agent.

Runs the stage-1 LLM evidence extraction step for each patent and attaches
structured evidence back onto the patent dict.
"""

import logging
from typing import Any

from app.services.gemini_service import GeminiService
from app.agents.patent_evaluation import evidence_level_to_fraction

logger = logging.getLogger(__name__)


async def analyze_patents(
    patents: list[dict[str, Any]],
    molecule_context: dict[str, Any],
    gemini_service: GeminiService | None = None,
) -> list[dict[str, Any]]:
    """
    Add structured evidence fields to each patent dict.

    Args:
        patents: List of enriched patent dicts.
        molecule_context: Dict with keys: smiles, target, disease.
        gemini_service: Injected GeminiService (or creates one).

    Returns:
        The same list with evidence fields populated.
    """
    if gemini_service is None:
        gemini_service = GeminiService()

    for patent in patents:
        patent_id = patent.get("patent_id", "UNKNOWN")
        try:
            evidence = await gemini_service.extract_patent_evidence(
                patent_data=patent,
                molecule_context=molecule_context,
            )
            patent["molecule_match_level"] = evidence.get("moleculeMatch", "Low")
            patent["target_match_level"] = evidence.get("targetMatch", "Low")
            patent["indication_match_level"] = evidence.get("indicationMatch", "Low")
            patent["mechanism_match_level"] = evidence.get("mechanismMatch", "Low")
            patent["novelty_concern_level"] = evidence.get("noveltyConcern", "Low")
            patent["confidence_label"] = evidence.get("confidence", "Low")
            patent["matched_factors"] = evidence.get("matchedFactors", [])
            patent["reason"] = evidence.get("reason", "")
            patent["ai_explanation"] = patent["reason"]
            patent["target_match"] = evidence_level_to_fraction(
                patent["target_match_level"]
            )
            patent["disease_match"] = evidence_level_to_fraction(
                patent["indication_match_level"]
            )
            logger.debug("Generated explanation for %s.", patent_id)
        except Exception as exc:
            logger.error(
                "Failed to generate explanation for %s: %s", patent_id, exc
            )
            fallback_reason = (
                f"Analysis unavailable for patent {patent_id} due to an "
                f"internal error. Please review this patent manually."
            )
            patent["molecule_match_level"] = "Low"
            patent["target_match_level"] = "Low"
            patent["indication_match_level"] = "Low"
            patent["mechanism_match_level"] = "Low"
            patent["novelty_concern_level"] = "Low"
            patent["confidence_label"] = "Low"
            patent["matched_factors"] = []
            patent["reason"] = fallback_reason
            patent["ai_explanation"] = (
                fallback_reason
            )
            patent["target_match"] = 0.0
            patent["disease_match"] = 0.0

    logger.info("Analysis complete for %d patent(s).", len(patents))
    return patents
