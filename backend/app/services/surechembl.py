"""
PatentPilot SureChEMBL Client.

Queries the SureChEMBL API for structurally-similar compounds and their
associated patent references.
"""

import asyncio
import logging
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class SureChEMBLClient:
    """Async client for the SureChEMBL chemical patent search API."""

    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (base_url or settings.SURECHEMBL_BASE_URL).rstrip("/")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def search_by_similarity(
        self,
        smiles: str,
        threshold: float = 0.7,
    ) -> list[dict[str, Any]]:
        """
        Search SureChEMBL for compounds structurally similar to *smiles*.

        Returns an empty list when the live API is unreachable or returns
        no results.

        Args:
            smiles: Query SMILES string.
            threshold: Tanimoto similarity threshold (0–1).

        Returns:
            List of dicts with keys: patent_id, title, similarity_score, source.
        """
        try:
            results = await self._query_structure_search(smiles, threshold)
            if results:
                logger.info(
                    "SureChEMBL API returned %d patent(s) for SMILES=%s",
                    len(results),
                    smiles[:40],
                )
                return results
            logger.info(
                "SureChEMBL structure search returned 0 results; trying exact chemical lookup."
            )
            fallback_results = await self._query_exact_chemical_lookup(smiles)
            if fallback_results:
                logger.info(
                    "SureChEMBL exact chemical lookup returned %d patent(s) for SMILES=%s",
                    len(fallback_results),
                    smiles[:40],
                )
                return fallback_results
            logger.info("SureChEMBL API returned 0 results.")
        except Exception as exc:
            logger.warning(
                "SureChEMBL structure search failed (%s); trying exact chemical lookup.",
                exc,
            )
            try:
                fallback_results = await self._query_exact_chemical_lookup(smiles)
                if fallback_results:
                    logger.info(
                        "SureChEMBL exact chemical lookup returned %d patent(s) for SMILES=%s",
                        len(fallback_results),
                        smiles[:40],
                    )
                    return fallback_results
            except Exception as fallback_exc:
                logger.warning(
                    "SureChEMBL exact chemical lookup also failed (%s).",
                    fallback_exc,
                )

        return []

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _query_structure_search(
        self,
        smiles: str,
        threshold: float,
    ) -> list[dict[str, Any]]:
        """Perform the documented SureChEMBL structure-search workflow."""
        search_hash = await self._create_structure_search(smiles, threshold)
        if not search_hash:
            return []

        structure_hits = await self._wait_for_structure_results(search_hash)
        if not structure_hits:
            return []

        patents: list[dict[str, Any]] = []
        seen_ids: set[str] = set()
        documents_cache: dict[str, list[dict[str, Any]]] = {}
        # First pass: spread the results across multiple structure hits so
        # similarity values do not collapse to the first chemical only.
        for hit in structure_hits[: settings.TOP_N_PATENTS]:
            if len(patents) >= settings.TOP_N_PATENTS:
                break

            chem_id = hit.get("chemical_id") or hit.get("id")
            if not chem_id:
                continue

            hit_similarity = float(hit.get("similarity") or 0.0)
            await self._append_documents_for_hit(
                chem_id=str(chem_id),
                hit_similarity=hit_similarity,
                patents=patents,
                seen_ids=seen_ids,
                documents_cache=documents_cache,
                max_docs=1,
            )

        # Second pass: fill any remaining slots with additional documents,
        # preserving the similarity score of the chemical hit they came from.
        if len(patents) < settings.TOP_N_PATENTS:
            for hit in structure_hits[: settings.TOP_N_PATENTS]:
                if len(patents) >= settings.TOP_N_PATENTS:
                    break

                chem_id = hit.get("chemical_id") or hit.get("id")
                if not chem_id:
                    continue

                hit_similarity = float(hit.get("similarity") or 0.0)
                await self._append_documents_for_hit(
                    chem_id=str(chem_id),
                    hit_similarity=hit_similarity,
                    patents=patents,
                    seen_ids=seen_ids,
                    documents_cache=documents_cache,
                    max_docs=settings.TOP_N_PATENTS,
                )

        return patents

    async def _query_exact_chemical_lookup(
        self,
        smiles: str,
    ) -> list[dict[str, Any]]:
        """Fallback to exact chemical lookup when structure search fails."""
        url = f"{self.base_url}/chemical/smiles/"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, params={"smiles": smiles})
            response.raise_for_status()
            data = response.json()

        chemicals = data.get("data", {})
        if not isinstance(chemicals, dict) or not chemicals:
            return []

        patents: list[dict[str, Any]] = []
        seen_ids: set[str] = set()
        documents_cache: dict[str, list[dict[str, Any]]] = {}

        for chem in chemicals.values():
            if not isinstance(chem, dict):
                continue

            chem_id = chem.get("chemical_id") or chem.get("id")
            if not chem_id:
                continue

            await self._append_documents_for_hit(
                chem_id=str(chem_id),
                hit_similarity=1.0,
                patents=patents,
                seen_ids=seen_ids,
                documents_cache=documents_cache,
                max_docs=settings.TOP_N_PATENTS,
            )

            if len(patents) >= settings.TOP_N_PATENTS:
                break

        return patents

    async def _append_documents_for_hit(
        self,
        chem_id: str,
        hit_similarity: float,
        patents: list[dict[str, Any]],
        seen_ids: set[str],
        documents_cache: dict[str, list[dict[str, Any]]],
        max_docs: int,
    ) -> None:
        """Append patent documents for a structure hit, using cached docs."""
        documents = documents_cache.get(chem_id)
        if documents is None:
            documents = await self._documents_for_chemical(chem_id)
            documents_cache[chem_id] = documents

        added = 0
        for doc in documents:
            doc_id = doc.get("docId") or doc.get("id")
            if not doc_id or doc_id in seen_ids:
                continue

            title = self._extract_document_title(doc)
            patents.append(
                {
                    "patent_id": doc_id,
                    "title": title,
                    "similarity_score": hit_similarity,
                    "source": "SureChEMBL",
                }
            )
            seen_ids.add(doc_id)
            added += 1

            if len(patents) >= settings.TOP_N_PATENTS or added >= max_docs:
                break

    async def _create_structure_search(
        self,
        smiles: str,
        threshold: float,
    ) -> str | None:
        """Start a structure search and return the SureChEMBL search hash."""
        url = f"{self.base_url}/search/structure"
        payload = {
            "StructureSearchRequest": {
                "struct": smiles,
                "structSearchType": "SIMILARITY",
                "maxResults": settings.TOP_N_PATENTS,
                "query": smiles,
            }
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()

        search_hash = data.get("data", {}).get("hash")
        if not search_hash:
            logger.warning("SureChEMBL search did not return a hash.")
            return None

        logger.info(
            "SureChEMBL structure search started (hash=%s, threshold=%.2f).",
            search_hash,
            threshold,
        )
        return str(search_hash)

    async def _wait_for_structure_results(
        self,
        search_hash: str,
    ) -> list[dict[str, Any]]:
        """Poll SureChEMBL until the structure search completes."""
        status_url = f"{self.base_url}/search/{search_hash}/status"
        results_url = f"{self.base_url}/search/{search_hash}/results"

        async with httpx.AsyncClient(timeout=30.0) as client:
            for _ in range(5):
                status_response = await client.get(status_url)
                status_response.raise_for_status()
                status_data = status_response.json().get("data", {})

                message = str(status_data.get("message", "")).lower()
                if "searching finished" in message:
                    break
                await asyncio.sleep(0.5)

            results_response = await client.get(
                results_url,
                params={"page": 1, "max_results": settings.TOP_N_PATENTS},
            )
            results_response.raise_for_status()
            results_data = results_response.json()

        structures = (
            results_data.get("data", {})
            .get("results", {})
            .get("structures", [])
        )
        if not isinstance(structures, list):
            return []
        return structures

    async def _documents_for_chemical(self, chemical_id: str) -> list[dict[str, Any]]:
        """Fetch patent documents associated with a SureChEMBL chemical."""
        url = f"{self.base_url}/search/documents_for_structures"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url,
                params={
                    "chemicalIds": chemical_id,
                    "page": 1,
                    "itemsPerPage": settings.TOP_N_PATENTS,
                },
            )
            response.raise_for_status()
            data = response.json()

        documents = (
            data.get("data", {})
            .get("results", {})
            .get("documents", [])
        )
        if not isinstance(documents, list):
            return []
        return documents

    @staticmethod
    def _extract_document_title(document: dict[str, Any]) -> str | None:
        """Extract the first English title from a SureChEMBL document payload."""
        metadata = document.get("metadata", {}) if isinstance(document, dict) else {}
        titles = metadata.get("titles", []) if isinstance(metadata, dict) else []

        for title_group in titles:
            if not isinstance(title_group, dict):
                continue
            for title in title_group.get("titles", []):
                if isinstance(title, str) and title.strip():
                    return title.strip()

        return document.get("docId")
