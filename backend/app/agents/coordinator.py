"""
PatentPilot Coordinator.

Orchestrates the end-to-end patent analysis pipeline:
    SMILES validation -> Retrieval -> Validation -> LLM evidence extraction
    -> Scoring -> Report -> Persistence
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException

from app.config import settings
from app.models.schemas import AnalysisRequest
from app.services.rdkit_service import validate_smiles, generate_molecule_svg
from app.services.surechembl import SureChEMBLClient
from app.services.gemini_service import GeminiService
from app.agents import retrieval, validation, analysis, report, history
from app.agents.patent_evaluation import (
    calculate_risk_level,
    calculate_risk_score,
    calculate_similarity_score,
    evidence_level_to_fraction,
)
from app.agents.scoring import compute_overall_recommendation, rank_patents

logger = logging.getLogger(__name__)


async def run_pipeline(request: AnalysisRequest) -> dict[str, Any]:
    """
    Execute the full patent analysis pipeline.

    Args:
        request: Validated AnalysisRequest from the API layer.

    Returns:
        Complete analysis dict (including the persisted id).
    """
    # Step 1: Validate SMILES
    is_valid, canonical_smiles = validate_smiles(request.smiles)
    if not is_valid or canonical_smiles is None:
        raise HTTPException(
            status_code=400,
            detail="Invalid SMILES string: could not parse molecular structure",
        )
    logger.info("Pipeline started for SMILES=%s", canonical_smiles)

    # Step 2: Initialise services
    surechembl_client = SureChEMBLClient()
    gemini_service = GeminiService()

    molecule_context: dict[str, Any] = {
        "smiles": canonical_smiles,
        "target": request.target,
        "disease": request.disease,
    }

    # Step 3: Retrieve patents
    patents = await retrieval.retrieve_patents(
        canonical_smiles,
        request.target,
        request.disease,
        threshold=settings.SIMILARITY_THRESHOLD,
        surechembl_client=surechembl_client,
    )

    # Step 4: Validate evidence (retry with lower thresholds)
    patents, evidence_sufficient = await validation.validate_evidence(
        patents,
        canonical_smiles,
        request.target,
        request.disease,
        retrieval.retrieve_patents,
        surechembl_client=surechembl_client,
    )

    # Step 5: Stage-1 evidence extraction
    patents = await analysis.analyze_patents(
        patents, molecule_context, gemini_service=gemini_service
    )

    # Step 6: Stage-2 backend scoring
    for patent in patents:
        evidence_payload = {
            "moleculeMatch": patent.get("molecule_match_level", "Low"),
            "targetMatch": patent.get("target_match_level", "Low"),
            "indicationMatch": patent.get("indication_match_level", "Low"),
            "mechanismMatch": patent.get("mechanism_match_level", "Low"),
        }

        patent["similarity_score"] = calculate_similarity_score(evidence_payload)
        patent["risk_label"] = calculate_risk_level(
            patent["similarity_score"], evidence_payload
        )
        patent["risk_score"] = calculate_risk_score(patent["risk_label"])
        patent["patent_score"] = patent["risk_score"]
        patent["target_match"] = evidence_level_to_fraction(
            patent.get("target_match_level", "Low")
        )
        patent["disease_match"] = evidence_level_to_fraction(
            patent.get("indication_match_level", "Low")
        )

    # Step 7: Rank by composite risk
    patents = rank_patents(patents)

    # Step 8: Overall recommendation
    patent_scores = [p.get("similarity_score", 0.0) for p in patents]
    overall_recommendation, recommendation_reasoning = (
        compute_overall_recommendation(patent_scores, evidence_sufficient)
    )

    # Step 9: Generate report
    report_data = await report.generate_report(
        patents,
        molecule_context,
        overall_recommendation,
        recommendation_reasoning,
        evidence_sufficient,
        gemini_service=gemini_service,
    )

    # Step 10: Assemble final document
    molecule_svg = generate_molecule_svg(canonical_smiles)
    analysis_doc: dict[str, Any] = {
        "submitted_smiles": request.smiles,
        "canonical_smiles": canonical_smiles,
        "target": request.target,
        "disease": request.disease,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "patents": patents,
        "evidence_sufficient": evidence_sufficient,
        "overall_recommendation": overall_recommendation,
        "recommendation_reasoning": recommendation_reasoning,
        "report": report_data,
        "molecule_svg": molecule_svg,
    }

    # Step 11: Persist to history
    try:
        doc_id = await history.save_analysis(analysis_doc)
        analysis_doc["id"] = doc_id
    except Exception as exc:
        logger.error("Failed to persist analysis: %s", exc)
        analysis_doc["id"] = "unsaved"

    logger.info(
        "Pipeline complete - id=%s, recommendation=%s, patents=%d",
        analysis_doc.get("id"),
        overall_recommendation,
        len(patents),
    )

    return analysis_doc
