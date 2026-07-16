"""
PatentPilot Retrieval Agent.

Orchestrates patent retrieval from SureChEMBL and keyword-based
target/disease matching.
"""

import logging
from typing import Any

from app.services.epo_ops import EPOOPSClient
from app.services.surechembl import SureChEMBLClient

logger = logging.getLogger(__name__)


def _build_patent_url(patent_id: str) -> str | None:
    """
    Build a Google Patents URL from a SureChEMBL document ID.

    Google Patents generally accepts the patent number without the dash
    between the country code and numeric portion, e.g. CN-104387360-B ->
    CN104387360B.
    """
    if not patent_id or patent_id == "UNKNOWN":
        return None

    normalized = patent_id.replace("-", "")
    return f"https://patents.google.com/patent/{normalized}/en"


def _keyword_overlap(query: str | None, text: str) -> float:
    """
    Compute simple keyword overlap between *query* and *text*.

    Returns the fraction of query words found in the text (case-insensitive).
    """
    if not query:
        return 0.0

    query_words = set(query.lower().split())
    if not query_words:
        return 0.0

    text_lower = text.lower()
    matches = sum(1 for w in query_words if w in text_lower)
    return round(matches / len(query_words), 4)


def _summarize_abstract(abstract: str | None, max_chars: int = 260) -> str | None:
    """Create a short, readable abstract preview without extra dependencies."""
    if not abstract:
        return None

    text = " ".join(abstract.split())
    if not text:
        return None

    sentence_endings = [". ", "! ", "? "]
    cut = len(text)
    for marker in sentence_endings:
        idx = text.find(marker)
        if idx != -1:
            cut = min(cut, idx + 1)

    preview = text[:cut].strip()
    if len(preview) > max_chars:
        preview = preview[: max_chars - 1].rstrip() + "…"
    return preview


async def retrieve_patents(
    canonical_smiles: str,
    target: str | None,
    disease: str | None,
    threshold: float = 0.7,
    surechembl_client: SureChEMBLClient | None = None,
    epo_client: EPOOPSClient | None = None,
) -> list[dict[str, Any]]:
    """
    Retrieve patents for *canonical_smiles*.

    Steps:
        1. Query SureChEMBL for structurally-similar compounds.
        2. Compute target_match and disease_match via keyword overlap.
        3. Return results sorted by similarity_score (descending).

    Args:
        canonical_smiles: Canonicalized SMILES of the query molecule.
        target: Optional biological target for keyword matching.
        disease: Optional disease area for keyword matching.
        threshold: Tanimoto similarity threshold for SureChEMBL query.
        surechembl_client: Injected SureChEMBL client (or creates one).

    Returns:
        List of SureChEMBL patent dicts with keyword match annotations.
    """
    if surechembl_client is None:
        surechembl_client = SureChEMBLClient()
    if epo_client is None:
        epo_client = EPOOPSClient()

    # Step 1 — SureChEMBL search
    logger.info(
        "Querying SureChEMBL (threshold=%.2f) for SMILES=%s …",
        threshold,
        canonical_smiles[:50],
    )
    raw_patents = await surechembl_client.search_by_similarity(
        canonical_smiles, threshold=threshold
    )
    logger.info("SureChEMBL returned %d candidate patent(s).", len(raw_patents))

    enriched: list[dict[str, Any]] = []

    for patent in raw_patents:
        patent_id = patent.get("patent_id", "UNKNOWN")
        title = patent.get("title")
        biblio = await epo_client.get_patent_biblio(patent_id)
        legal_status = await epo_client.get_legal_status(patent_id)
        abstract = biblio.get("abstract") if isinstance(biblio, dict) else None
        if not abstract and hasattr(epo_client, "get_google_patent_abstract"):
            abstract = await epo_client.get_google_patent_abstract(patent_id)
        abstract_summary = _summarize_abstract(abstract)

        enriched_patent: dict[str, Any] = {
            "patent_id": patent_id,
            "source": patent.get("source", "SureChEMBL"),
            "title": biblio.get("title") if isinstance(biblio, dict) and biblio.get("title") else title,
            "patent_url": _build_patent_url(patent_id),
            "raw_similarity_score": float(patent.get("similarity_score", 0.0)),
            "abstract": abstract,
            "abstract_summary": abstract_summary,
            "assignee": biblio.get("assignee") if isinstance(biblio, dict) else None,
            "pub_date": biblio.get("pub_date") if isinstance(biblio, dict) else None,
            "legal_status": legal_status,
            "similarity_score": float(patent.get("similarity_score", 0.0)),
        }

        searchable_text = " ".join(
            filter(None, [enriched_patent["title"], abstract_summary, abstract])
        )
        enriched_patent["target_match"] = _keyword_overlap(target, searchable_text)
        enriched_patent["disease_match"] = _keyword_overlap(disease, searchable_text)

        enriched.append(enriched_patent)

    # Step 3 — sort by similarity descending
    enriched.sort(key=lambda p: p.get("similarity_score", 0.0), reverse=True)

    logger.info("Retrieval complete: %d enriched patent(s).", len(enriched))
    return enriched
