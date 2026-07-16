"""
PatentPilot Validation Agent.

Ensures that the patent evidence base meets the minimum threshold
(≥ 3 patents). If not, progressively lowers the similarity threshold
and retries retrieval.
"""

import logging
from typing import Any, Callable, Coroutine

logger = logging.getLogger(__name__)

# Type alias for the retrieval function
RetrievalFunc = Callable[..., Coroutine[Any, Any, list[dict[str, Any]]]]


async def validate_evidence(
    patents: list[dict[str, Any]],
    canonical_smiles: str,
    target: str | None,
    disease: str | None,
    retrieval_func: RetrievalFunc,
    **retrieval_kwargs: Any,
) -> tuple[list[dict[str, Any]], bool]:
    """
    Validate that the evidence base is sufficient (≥ 3 patents).

    If the initial set contains fewer than 3 patents, the retrieval
    is retried with progressively lower similarity thresholds:
        Retry 1 → threshold 0.5
        Retry 2 → threshold 0.3

    Patents are deduplicated by patent_id across retries.

    Args:
        patents: Initial patent list from the first retrieval pass.
        canonical_smiles: Canonical SMILES string.
        target: Optional biological target.
        disease: Optional disease area.
        retrieval_func: The async retrieval function to call for retries.
        **retrieval_kwargs: Extra keyword arguments forwarded to the
            retrieval function (e.g. surechembl_client, epo_client).

    Returns:
        (final_patents, evidence_sufficient)
    """
    seen_ids: set[str] = set()
    merged: list[dict[str, Any]] = []

    def _merge(new_patents: list[dict[str, Any]]) -> None:
        for p in new_patents:
            pid = p.get("patent_id", "")
            if pid and pid not in seen_ids:
                seen_ids.add(pid)
                merged.append(p)

    _merge(patents)

    if len(merged) >= 3:
        logger.info("Evidence sufficient: %d patent(s) found.", len(merged))
        return (merged, True)

    # Retry 1 — lower threshold to 0.5
    logger.info(
        "Insufficient evidence (%d patents). Retrying with threshold=0.5 …",
        len(merged),
    )
    retry1 = await retrieval_func(
        canonical_smiles,
        target,
        disease,
        threshold=0.5,
        **retrieval_kwargs,
    )
    _merge(retry1)

    if len(merged) >= 3:
        logger.info(
            "Evidence sufficient after retry 1: %d patent(s).", len(merged)
        )
        return (merged, True)

    # Retry 2 — lower threshold to 0.3
    logger.info(
        "Still insufficient (%d patents). Retrying with threshold=0.3 …",
        len(merged),
    )
    retry2 = await retrieval_func(
        canonical_smiles,
        target,
        disease,
        threshold=0.3,
        **retrieval_kwargs,
    )
    _merge(retry2)

    evidence_sufficient = len(merged) >= 3

    if evidence_sufficient:
        logger.info(
            "Evidence sufficient after retry 2: %d patent(s).", len(merged)
        )
    else:
        logger.warning(
            "Evidence INSUFFICIENT after all retries: only %d patent(s).",
            len(merged),
        )

    return (merged, evidence_sufficient)
