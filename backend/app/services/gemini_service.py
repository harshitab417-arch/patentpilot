"""
PatentPilot Gemini Service.

Integrates with the Google Gemini generative AI API to produce
strictly-grounded patent analysis explanations and report summaries.
"""

import json
import logging
import os
import re
from typing import Any

from app.agents.patent_evaluation import normalize_evidence_level
from app.config import settings

logger = logging.getLogger(__name__)


class GeminiAnalysisError(RuntimeError):
    """Base error for Gemini evidence generation failures."""


class GeminiQuotaExceededError(GeminiAnalysisError):
    """Raised when Gemini reports a 429 RESOURCE_EXHAUSTED error."""


class GeminiService:
    """Client for the Google Gemini generative AI API."""

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self.api_key = self._resolve_api_key(api_key)
        self.model_name = model or settings.GEMINI_MODEL
        self._client: Any = None

        key_present = bool(self.api_key and self.api_key.strip())
        logger.info(
            "Gemini configuration resolved: key_present=%s, model=%s",
            key_present,
            self.model_name,
        )

        if not key_present:
            logger.warning(
                "Gemini API key is missing or empty; falling back to local heuristic analysis."
            )
            return

        try:
            from google import genai

            self._client = genai.Client(api_key=self.api_key)
            logger.info("Gemini client initialized (model=%s).", self.model_name)
        except Exception as exc:
            logger.warning("Failed to initialise Gemini client: %s", exc)
            self._client = None

    @staticmethod
    def _resolve_api_key(api_key: str | None = None) -> str:
        if api_key and api_key.strip():
            return api_key.strip()

        for env_name in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
            env_value = os.getenv(env_name)
            if env_value and env_value.strip():
                return env_value.strip()

        configured_value = getattr(settings, "GEMINI_API_KEY", "") or ""
        return configured_value.strip()

    # ------------------------------------------------------------------
    # Patent explanation
    # ------------------------------------------------------------------

    async def generate_patent_explanation(
        self,
        patent_data: dict[str, Any],
        molecule_context: dict[str, Any],
    ) -> str:
        """
        Generate a grounded explanation of why a patent is relevant
        to the submitted molecule.
        """
        prompt = self._build_explanation_prompt(patent_data, molecule_context)

        if self._client is not None:
            try:
                response = self._client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                )
                text = response.text
                if text:
                    return text.strip()
            except Exception as exc:
                logger.error("Gemini explanation call failed: %s", exc)

        # Template fallback
        return self._template_explanation(patent_data, molecule_context)

    async def extract_patent_evidence(
        self,
        patent_data: dict[str, Any],
        molecule_context: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Extract structured evidence labels for a patent.

        The LLM must return JSON only. If the model is unavailable or the
        response cannot be parsed, a deterministic fallback is used.
        """
        prompt = self._build_evidence_prompt(patent_data, molecule_context)

        if self._client is None:
            raise RuntimeError(
                "Gemini client is unavailable. Verify GEMINI_API_KEY and SDK setup."
            )

        try:
            response = self._client.models.generate_content(
                model=self.model_name,
                contents=prompt,
            )
        except Exception as exc:
            if self._is_quota_error(exc):
                logger.warning(
                    "Gemini quota exceeded for patent %s; using local heuristic fallback.",
                    patent_data.get("patent_id", "N/A"),
                )
                return self._local_heuristic_evidence(
                    patent_data,
                    molecule_context,
                    fallback_reason="Local heuristic analysis (Gemini unavailable due to quota).",
                    analysis_status={
                        "state": "degraded",
                        "source": "local_heuristic",
                        "reason": "Gemini unavailable due to quota",
                    },
                )

            message = str(exc)
            if "API key not valid" in message or "API_KEY_INVALID" in message:
                raise RuntimeError(
                    "Invalid GEMINI_API_KEY. Update backend/.env with a valid "
                    "Gemini API key."
                ) from exc

            logger.error(
                "Gemini evidence extraction failed for patent %s: %s",
                patent_data.get("patent_id", "N/A"),
                exc,
            )
            return self._local_heuristic_evidence(
                patent_data,
                molecule_context,
                fallback_reason="Local heuristic analysis (Gemini unavailable).",
                analysis_status={
                    "state": "degraded",
                    "source": "local_heuristic",
                    "reason": "Gemini unavailable",
                },
            )

        text = response.text
        if not text:
            logger.warning(
                "Gemini returned an empty response for patent %s; using local heuristic fallback.",
                patent_data.get("patent_id", "N/A"),
            )
            return self._local_heuristic_evidence(
                patent_data,
                molecule_context,
                fallback_reason="Local heuristic analysis (Gemini returned an empty response).",
                analysis_status={
                    "state": "degraded",
                    "source": "local_heuristic",
                    "reason": "Gemini returned an empty response",
                },
            )

        parsed = self._parse_evidence_response(text)
        if not parsed:
            logger.warning(
                "Gemini returned non-JSON evidence for patent %s; using local heuristic fallback.",
                patent_data.get("patent_id", "N/A"),
            )
            return self._local_heuristic_evidence(
                patent_data,
                molecule_context,
                fallback_reason="Local heuristic analysis (Gemini response was not valid JSON).",
                analysis_status={
                    "state": "degraded",
                    "source": "local_heuristic",
                    "reason": "Gemini response was not valid JSON",
                },
            )

        return parsed

    # ------------------------------------------------------------------
    # Report summary
    # ------------------------------------------------------------------

    async def generate_report_summary(
        self,
        analysis_data: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Generate a structured report summary from the full analysis.

        Returns dict with keys: executive_summary, novelty_concerns,
        manual_review_reasoning.
        """
        prompt = self._build_report_prompt(analysis_data)

        if self._client is not None:
            try:
                response = self._client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                )
                text = response.text
                if text:
                    parsed = self._parse_report_response(text)
                    if parsed:
                        return parsed
            except Exception as exc:
                if self._is_quota_error(exc):
                    logger.warning(
                        "Gemini quota exceeded while generating report summary; using local fallback."
                    )
                else:
                    logger.error("Gemini report summary call failed: %s", exc)

        # Template fallback
        return self._template_report(analysis_data)

    # ------------------------------------------------------------------
    # Prompt builders
    # ------------------------------------------------------------------

    @staticmethod
    def _build_explanation_prompt(
        patent_data: dict[str, Any],
        molecule_context: dict[str, Any],
    ) -> str:
        return (
            "You are an expert patent analyst. Based ONLY on the following "
            "retrieved patent data, provide a concise analysis for a "
            "pharmaceutical researcher.\n\n"
            "MOLECULE CONTEXT:\n"
            f"- SMILES: {molecule_context.get('smiles', 'N/A')}\n"
            f"- Target: {molecule_context.get('target') or 'Not specified'}\n"
            f"- Disease: {molecule_context.get('disease') or 'Not specified'}\n\n"
            "PATENT DATA:\n"
            f"- Patent ID: {patent_data.get('patent_id', 'N/A')}\n"
            f"- Title: {patent_data.get('title') or 'Not available'}\n"
            f"- Abstract: {patent_data.get('abstract') or 'Not available'}\n"
            f"- Abstract Summary: {patent_data.get('abstract_summary') or 'Not available'}\n"
            f"- Assignee: {patent_data.get('assignee') or 'Not available'}\n"
            f"- Legal Status: {patent_data.get('legal_status') or 'Not available'}\n"
            f"- Similarity Score: {patent_data.get('similarity_score', 0.0)}\n"
            f"- Risk Score: {patent_data.get('risk_score', patent_data.get('patent_score', 0.0))}\n"
            f"- Abstract Summary: {patent_data.get('abstract_summary') or 'Not available'}\n"
            f"- Computed Confidence: {patent_data.get('confidence_label', 'Low')}\n\n"
            "Your explanation must be patent-specific and should not reuse the same "
            "generic wording across different patents.\n"
            "Before writing, identify the concrete concepts explicitly supported by "
            "the title and abstract, such as:\n"
            "- molecule type\n"
            "- biological target\n"
            "- therapeutic indication\n"
            "- chemical scaffold\n"
            "- formulation\n"
            "- synthesis\n"
            "- mechanism of action\n"
            "- agricultural application\n"
            "- antibody engineering\n"
            "- delivery mechanism\n\n"
            "Use only concepts that are actually present or clearly implied by the "
            "patent title/abstract. Reference at least two patent-specific terms or "
            "phrases from the title/abstract when possible.\n\n"
            "Provide:\n"
            "1. WHY this patent was retrieved (structural similarity basis)\n"
            "2. Which specific title/abstract concepts overlap with the submitted molecule\n"
            "3. NOVELTY CONCERN assessment tied to those concepts\n"
            "4. Any GAPS in available data that limit the analysis\n\n"
            "CRITICAL RULES:\n"
            "- If any field is 'Not available', explicitly state you cannot "
            "assess that dimension. Do NOT speculate or fabricate information.\n"
            "- Reference ONLY the actual data provided above.\n"
            "- Be specific, not generic. Mention actual molecular features "
            "or patent concepts if apparent from the title or abstract.\n"
            "- Prefer wording that distinguishes this patent from other hits by "
            "naming its particular chemistry, target, indication, platform, or "
            "use case.\n"
            "- Do not write a boilerplate sentence that could apply to any patent.\n"
            "- Keep response under 200 words."
        )

    @staticmethod
    def _build_evidence_prompt(
        patent_data: dict[str, Any],
        molecule_context: dict[str, Any],
    ) -> str:
        return (
            "You are an expert patent analyst.\n"
            "Evaluate the relationship between the user query and the patent.\n"
            "Return JSON only. Do not include markdown, code fences, or extra text.\n\n"
            "USER QUERY:\n"
            f"- Molecule: {molecule_context.get('smiles', 'N/A')}\n"
            f"- Biological Target: {molecule_context.get('target') or 'Not specified'}\n"
            f"- Disease / Indication: {molecule_context.get('disease') or 'Not specified'}\n\n"
            "PATENT:\n"
            f"- Publication Number: {patent_data.get('patent_id', 'N/A')}\n"
            f"- Title: {patent_data.get('title') or 'Not available'}\n"
            f"- Abstract: {patent_data.get('abstract') or patent_data.get('abstract_summary') or 'Not available'}\n"
            f"- Publication Date: {patent_data.get('pub_date') or 'Not available'}\n\n"
            "Write a patent-specific reason that clearly reflects concepts found in "
            "the title and abstract. Anchor the explanation in the exact patent "
            "domain, for example molecule type, biological target, therapeutic "
            "indication, chemical scaffold, formulation, synthesis, mechanism of "
            "action, agricultural application, antibody engineering, or delivery "
            "mechanism, but only if those concepts are actually supported by the "
            "patent text.\n"
            "The reason should vary across patents and must not sound generic. "
            "It should name the most relevant title/abstract concept(s) and explain "
            "how they relate to the query.\n\n"
            "Return exactly this JSON shape:\n"
            "{\n"
            '  "moleculeMatch": "Low|Medium|High",\n'
            '  "targetMatch": "Low|Medium|High",\n'
            '  "indicationMatch": "Low|Medium|High",\n'
            '  "mechanismMatch": "Low|Medium|High",\n'
            '  "noveltyConcern": "Low|Medium|High",\n'
            '  "confidence": "Low|Medium|High",\n'
            '  "reason": "short explanation",\n'
            '  "matchedFactors": ["factor 1", "factor 2"]\n'
            "}\n\n"
            "Rules:\n"
            "- Use only Low, Medium, or High for the level fields.\n"
            "- Do not output similarity percentages or numeric risk values.\n"
            "- Base the decision on the patent title and abstract, plus the query.\n"
            "- In the reason, explicitly name the patent concepts that support the "
            "assessment instead of using a generic fallback phrase.\n"
            "- If the title/abstract point to a different domain than the query, say "
            "so directly and mention the domain difference.\n"
            "- If evidence is weak or incomplete, lower confidence instead of guessing.\n"
            "- Keep the reason concise and specific."
        )

    @staticmethod
    def _build_report_prompt(analysis_data: dict[str, Any]) -> str:
        patents_summary = ""
        for p in analysis_data.get("patents", []):
            patents_summary += (
                f"  - {p.get('patent_id')}: risk={p.get('risk_score', p.get('patent_score', 0)):.2f}, "
                f"similarity={p.get('similarity_score', 0):.2f}, "
                f"confidence={p.get('confidence_label', 'Low')}, "
                f"title={p.get('title', 'N/A')}\n"
            )

        return (
            "You are an expert patent analyst. Based ONLY on the data below, "
            "produce a structured patent landscape analysis report.\n\n"
            f"MOLECULE: {analysis_data.get('canonical_smiles', 'N/A')}\n"
            f"Target: {analysis_data.get('target') or 'Not specified'}\n"
            f"Disease: {analysis_data.get('disease') or 'Not specified'}\n"
            f"Overall Recommendation: {analysis_data.get('overall_recommendation', 'N/A')}\n"
            f"Evidence Sufficient: {analysis_data.get('evidence_sufficient', False)}\n\n"
            f"PATENTS:\n{patents_summary}\n"
            "Produce the following in JSON format:\n"
            "{\n"
            '  "executive_summary": "<2-3 paragraph summary>",\n'
            '  "novelty_concerns": ["<concern 1>", "<concern 2>", ...],\n'
            '  "manual_review_reasoning": "<why manual review is/isn\'t needed>"\n'
            "}\n\n"
            "RULES:\n"
            "- Reference ONLY provided data. Do NOT fabricate patent IDs or scores.\n"
            "- If evidence is insufficient, state this clearly.\n"
            "- Keep executive_summary under 300 words."
        )

    # ------------------------------------------------------------------
    # Response parsing
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_report_response(text: str) -> dict[str, Any] | None:
        """Attempt to parse Gemini's response as JSON."""
        # Try extracting JSON from markdown code blocks
        json_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
        raw = json_match.group(1) if json_match else text

        try:
            data = json.loads(raw)
            return {
                "executive_summary": data.get("executive_summary", ""),
                "novelty_concerns": data.get("novelty_concerns", []),
                "manual_review_reasoning": data.get("manual_review_reasoning", ""),
            }
        except (json.JSONDecodeError, TypeError):
            logger.warning("Could not parse Gemini report response as JSON.")
            return None

    @staticmethod
    def _parse_evidence_response(text: str) -> dict[str, Any] | None:
        """Attempt to parse Gemini's evidence JSON response."""
        json_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
        raw = json_match.group(1) if json_match else text

        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            logger.warning("Could not parse Gemini evidence response as JSON.")
            return None

        if not isinstance(data, dict):
            return None

        matched_factors = data.get("matchedFactors", [])
        if not isinstance(matched_factors, list):
            matched_factors = []

        return {
            "moleculeMatch": normalize_evidence_level(data.get("moleculeMatch")),
            "targetMatch": normalize_evidence_level(data.get("targetMatch")),
            "indicationMatch": normalize_evidence_level(data.get("indicationMatch")),
            "mechanismMatch": normalize_evidence_level(data.get("mechanismMatch")),
            "noveltyConcern": normalize_evidence_level(data.get("noveltyConcern")),
            "confidence": normalize_evidence_level(data.get("confidence")),
            "reason": str(data.get("reason", "")).strip(),
            "matchedFactors": [
                str(item).strip() for item in matched_factors if str(item).strip()
            ],
            "analysisMode": "gemini",
        }

    @staticmethod
    def _is_quota_error(exc: Exception) -> bool:
        """Return True when Gemini reports a 429 RESOURCE_EXHAUSTED error."""
        status_code = getattr(exc, "status_code", None)
        if status_code == 429:
            return True

        response = getattr(exc, "response", None)
        if getattr(response, "status_code", None) == 429:
            return True

        message = str(exc).upper()
        return "RESOURCE_EXHAUSTED" in message or "QUOTA EXCEEDED" in message

    @staticmethod
    def _tokenize(text: str) -> set[str]:
        tokens = {
            token
            for token in re.findall(r"[a-z0-9]+", text.lower())
            if len(token) > 2
        }
        stopwords = {
            "the",
            "and",
            "with",
            "from",
            "that",
            "this",
            "for",
            "use",
            "used",
            "method",
            "device",
            "composition",
            "patent",
            "invention",
            "present",
            "relates",
            "relating",
        }
        return {token for token in tokens if token not in stopwords}

    @classmethod
    def _local_heuristic_evidence(
        cls,
        patent_data: dict[str, Any],
        molecule_context: dict[str, Any],
        fallback_reason: str,
        analysis_status: dict[str, Any],
    ) -> dict[str, Any]:
        title = (patent_data.get("title") or "").strip()
        abstract = (
            patent_data.get("abstract")
            or patent_data.get("abstract_summary")
            or ""
        ).strip()
        searchable = f"{title} {abstract}".lower()

        target = (molecule_context.get("target") or "").strip().lower()
        disease = (molecule_context.get("disease") or "").strip().lower()
        smiles = molecule_context.get("smiles") or ""

        target_hit = bool(target and target in searchable)
        disease_hit = bool(disease and disease in searchable)

        concept_hits: list[str] = []
        concept_map = [
            (
                "chemical matter / scaffold",
                (
                    "compound",
                    "derivative",
                    "analog",
                    "analogue",
                    "scaffold",
                    "molecule",
                    "formula",
                    "pharmaceutical composition",
                ),
            ),
            (
                "formulation / dosage form",
                (
                    "formulation",
                    "dosage",
                    "tablet",
                    "capsule",
                    "suspension",
                    "solution",
                    "release",
                    "oral",
                    "injectable",
                ),
            ),
            (
                "synthesis / preparation",
                (
                    "synthesis",
                    "synthetic",
                    "preparation",
                    "manufacture",
                    "process",
                    "method of preparing",
                ),
            ),
            (
                "delivery mechanism",
                (
                    "delivery",
                    "carrier",
                    "insert",
                    "device",
                    "release mechanism",
                    "administration",
                ),
            ),
            (
                "mechanism of action",
                (
                    "inhibitor",
                    "agonist",
                    "antagonist",
                    "modulator",
                    "binder",
                    "pathway",
                    "receptor",
                    "enzyme",
                ),
            ),
            (
                "antibody engineering",
                (
                    "antibody",
                    "antigen",
                    "epitope",
                    "humanized",
                    "chimeric",
                    "fc",
                ),
            ),
            (
                "agricultural application",
                (
                    "agricultural",
                    "crop",
                    "plant",
                    "herbicid",
                    "fungicid",
                    "pesticid",
                    "weed",
                ),
            ),
        ]

        for label, keywords in concept_map:
            if any(keyword in searchable for keyword in keywords):
                concept_hits.append(label)

        query_terms = cls._tokenize(" ".join(filter(None, [target, disease, smiles])))
        patent_terms = cls._tokenize(f"{title} {abstract}")
        shared_terms = sorted(term for term in query_terms if term in patent_terms)

        if target_hit:
            concept_hits.append("biological target match")
        if disease_hit:
            concept_hits.append("therapeutic indication match")
        if shared_terms:
            concept_hits.append(f"shared query terms: {', '.join(shared_terms[:3])}")
        if smiles and not concept_hits:
            concept_hits.append("limited query overlap from submitted SMILES context")

        if target_hit and disease_hit:
            molecule_match = "High"
            target_match = "High"
            indication_match = "High"
        elif target_hit or disease_hit or len(shared_terms) >= 2:
            molecule_match = "Medium"
            target_match = "High" if target_hit else "Medium"
            indication_match = "High" if disease_hit else "Medium"
        elif concept_hits:
            molecule_match = "Medium"
            target_match = "Medium"
            indication_match = "Medium"
        else:
            molecule_match = "Low"
            target_match = "Low"
            indication_match = "Low"

        mechanism_match = (
            "High" if any("mechanism" in hit or "target match" in hit for hit in concept_hits) else
            "Medium" if any(
                label in concept_hits
                for label in (
                    "chemical matter / scaffold",
                    "formulation / dosage form",
                    "delivery mechanism",
                    "synthesis / preparation",
                )
            ) else "Low"
        )

        novelty = "High" if concept_hits and (target_hit or disease_hit) else "Medium" if concept_hits else "Low"
        confidence = "Medium" if concept_hits else "Low"

        reason_parts = [fallback_reason]
        if title:
            reason_parts.append(f"Title: {title}.")
        if abstract:
            reason_parts.append(f"Abstract: {abstract[:240].rstrip()}{'...' if len(abstract) > 240 else ''}")
        if concept_hits:
            reason_parts.append("Matched concepts: " + "; ".join(dict.fromkeys(concept_hits)))
        if target_hit or disease_hit:
            query_bits = []
            if target_hit:
                query_bits.append(f"target '{molecule_context.get('target')}'")
            if disease_hit:
                query_bits.append(f"indication '{molecule_context.get('disease')}'")
            reason_parts.append("Query overlap: " + ", ".join(query_bits) + ".")
        else:
            reason_parts.append("Query overlap is limited, so the analysis stays conservative.")

        return {
            "moleculeMatch": molecule_match,
            "targetMatch": target_match,
            "indicationMatch": indication_match,
            "mechanismMatch": mechanism_match,
            "noveltyConcern": novelty,
            "confidence": confidence,
            "reason": " ".join(part.strip() for part in reason_parts if part.strip()),
            "matchedFactors": concept_hits or ["Limited query overlap"],
            "analysisMode": "local_heuristic",
            "analysisStatus": analysis_status,
        }

    # ------------------------------------------------------------------
    # Template fallbacks
    # ------------------------------------------------------------------

    @staticmethod
    def _template_explanation(
        patent_data: dict[str, Any],
        molecule_context: dict[str, Any],
    ) -> str:
        pid = patent_data.get("patent_id", "Unknown")
        sim = float(patent_data.get("similarity_score", 0.0))
        sim_percent = sim * 100 if sim <= 1.0 else sim
        title = patent_data.get("title") or "Not available"
        legal = patent_data.get("legal_status") or "Not available"
        confidence = patent_data.get("confidence_label", "Low")

        lines = [
            f"**Patent {pid}** (Confidence: {confidence})",
            "",
            f"This patent was retrieved due to a structural similarity score of "
            f"{sim_percent:.0f} with the submitted molecule "
            f"({molecule_context.get('smiles', 'N/A')}).",
            "",
            f"Title: {title}",
            f"Legal Status: {legal}",
            "",
        ]

        if sim_percent >= 85:
            lines.append(
                "HIGH OVERLAP: The similarity score suggests significant overlap. "
                "A detailed freedom-to-operate analysis is recommended."
            )
        elif sim_percent >= 60:
            lines.append(
                "MODERATE OVERLAP: Some evidence overlaps. Expert review is "
                "advisable to evaluate claim scope."
            )
        else:
            lines.append(
                "LOW OVERLAP: Limited similarity detected. "
                "Risk appears low based on available data."
            )

        if legal == "Not available":
            lines.append(
                "\n📋 NOTE: Legal status data is unavailable, which limits "
                "the assessment of enforceability."
            )

        lines.append(
            "\n*This is a template-based analysis. Configure GEMINI_API_KEY "
            "for AI-powered insights.*"
        )

        return "\n".join(lines)

    @staticmethod
    def _template_evidence(
        patent_data: dict[str, Any],
        molecule_context: dict[str, Any],
    ) -> dict[str, Any]:
        title = (patent_data.get("title") or "").lower()
        abstract = (patent_data.get("abstract") or patent_data.get("abstract_summary") or "").lower()
        searchable = f"{title} {abstract}"

        target = (molecule_context.get("target") or "").lower()
        disease = (molecule_context.get("disease") or "").lower()
        smiles = molecule_context.get("smiles") or ""

        target_hit = bool(target and target in searchable)
        disease_hit = bool(disease and disease in searchable)
        mechanism_hit = any(
            keyword in searchable
            for keyword in (
                "mechanism",
                "pathway",
                "inhibitor",
                "agonist",
                "antagonist",
                "modulator",
                "binder",
                "derivative",
                "compound",
                "analog",
            )
        )
        molecule_hit = any(
            keyword in searchable
            for keyword in (
                "compound",
                "composition",
                "derivative",
                "analog",
                "analogs",
                "analogue",
                "scaffold",
                "formula",
            )
        )

        matched_factors: list[str] = []
        if target_hit:
            matched_factors.append("Same biological target mentioned")
        if disease_hit:
            matched_factors.append("Same therapeutic indication mentioned")
        if mechanism_hit:
            matched_factors.append("Shared mechanism language")
        if molecule_hit:
            matched_factors.append("Patent describes related chemical matter")

        if not matched_factors and smiles:
            matched_factors.append("Patent relevant to the submitted molecule context")

        if target_hit and disease_hit:
            confidence = "High"
        elif target_hit or disease_hit or mechanism_hit:
            confidence = "Medium"
        else:
            confidence = "Low"

        if disease_hit and molecule_hit:
            novelty = "High"
        elif target_hit or mechanism_hit:
            novelty = "Medium"
        else:
            novelty = "Low"

        if target_hit and disease_hit and molecule_hit:
            molecule_match = "High"
        elif molecule_hit or mechanism_hit:
            molecule_match = "Medium"
        else:
            molecule_match = "Low"

        return {
            "moleculeMatch": molecule_match,
            "targetMatch": "High" if target_hit else "Medium" if mechanism_hit else "Low",
            "indicationMatch": "High" if disease_hit else "Medium" if mechanism_hit else "Low",
            "mechanismMatch": "High" if mechanism_hit else "Low",
            "noveltyConcern": novelty,
            "confidence": confidence,
            "reason": (
                "Fallback evidence extracted from patent title and abstract. "
                "The patent shows "
                f"{'strong' if molecule_match == 'High' else 'moderate' if molecule_match == 'Medium' else 'limited'} "
                "chemical relevance and "
                f"{'clear' if target_hit or disease_hit else 'limited'} query overlap."
            ),
            "matchedFactors": matched_factors,
        }

    @staticmethod
    def _template_report(analysis_data: dict[str, Any]) -> dict[str, Any]:
        patents = analysis_data.get("patents", [])
        recommendation = analysis_data.get("overall_recommendation", "Unknown")
        evidence = analysis_data.get("evidence_sufficient", False)

        high_risk = [
            p
            for p in patents
            if p.get("risk_label") == "High"
            or float(p.get("similarity_score", 0.0)) >= 85.0
        ]
        n_patents = len(patents)

        summary_parts = [
            f"Patent landscape analysis identified {n_patents} potentially "
            f"relevant patent(s) for the submitted molecule "
            f"({analysis_data.get('canonical_smiles', 'N/A')}).",
        ]

        if not evidence:
            summary_parts.append(
                "WARNING: Fewer than 3 patents were retrieved. The evidence "
                "base is insufficient for a reliable assessment. Absence of "
                "patent matches does NOT guarantee freedom to operate."
            )

        summary_parts.append(f"Overall recommendation: {recommendation}.")

        if high_risk:
            summary_parts.append(
                f"{len(high_risk)} patent(s) scored above the high-risk "
                f"threshold and warrant detailed expert review."
            )

        concerns: list[str] = []
        for p in patents:
            similarity = float(p.get("similarity_score", 0.0))
            if similarity <= 1.0:
                similarity *= 100.0
            if similarity >= 85.0:
                concerns.append(
                    f"Patent {p.get('patent_id')} shows high similarity ({similarity:.0f})."
                )

        if not concerns:
            concerns.append(
                "No individual patents exceed the high-similarity threshold."
            )

        return {
            "executive_summary": " ".join(summary_parts),
            "novelty_concerns": concerns,
            "manual_review_reasoning": (
                f"Based on the {recommendation.lower()} assessment, "
                f"{'manual expert review is strongly recommended' if recommendation != 'Low Patent Risk' else 'routine monitoring is suggested'}."
            ),
        }
