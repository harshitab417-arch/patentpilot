"""
PatentPilot Pydantic Schemas.

Defines request/response models for the API layer.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class AnalysisRequest(BaseModel):
    """Request body for initiating a patent analysis."""

    smiles: str = Field(..., description="SMILES string of the molecule to analyze")
    target: str | None = Field(default=None, description="Biological target (e.g., 'EGFR', 'VEGFR2')")
    disease: str | None = Field(default=None, description="Disease area (e.g., 'lung cancer', 'diabetes')")


class PatentResult(BaseModel):
    """Individual patent result with scoring and AI analysis."""

    patent_id: str
    source: str
    title: str | None = None
    patent_url: str | None = None
    raw_similarity_score: float = 0.0
    pub_date: str | None = None
    assignee: str | None = None
    abstract: str | None = None
    abstract_summary: str | None = None
    legal_status: str | None = None
    similarity_score: float
    target_match: float = 0.0
    disease_match: float = 0.0
    molecule_match_level: str = "Low"
    target_match_level: str = "Low"
    indication_match_level: str = "Low"
    mechanism_match_level: str = "Low"
    novelty_concern_level: str = "Low"
    risk_score: float = 0.0
    patent_score: float = 0.0
    risk_label: str = "Low"
    confidence_label: str = "Low"
    matched_factors: list[str] = Field(default_factory=list)
    reason: str = ""
    ai_explanation: str = ""


class ReportData(BaseModel):
    """Structured report output from the analysis pipeline."""

    executive_summary: str
    key_patents: list[str]
    novelty_concerns: list[str]
    manual_review_list: list[str]


class AnalysisResponse(BaseModel):
    """Full analysis response returned to the client."""

    id: str
    submitted_smiles: str
    canonical_smiles: str
    target: str | None = None
    disease: str | None = None
    created_at: str
    patents: list[PatentResult]
    evidence_sufficient: bool
    overall_recommendation: str
    recommendation_reasoning: str
    report: ReportData
    molecule_svg: str | None = None


class AnalysisListItem(BaseModel):
    """Summary item for listing past analyses."""

    id: str
    submitted_smiles: str
    canonical_smiles: str
    target: str | None = None
    disease: str | None = None
    overall_recommendation: str
    created_at: str
    patent_count: int
