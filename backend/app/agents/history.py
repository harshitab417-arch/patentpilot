"""
PatentPilot History Agent.

Persists and retrieves analysis records from MongoDB.
"""

import logging
from typing import Any

from bson import ObjectId

from app.models.database import get_analyses_collection

logger = logging.getLogger(__name__)


async def save_analysis(analysis_data: dict[str, Any]) -> str:
    """
    Insert an analysis document into MongoDB.

    Args:
        analysis_data: Full analysis dict (without ``_id``).

    Returns:
        The string representation of the inserted document ID.
    """
    collection = get_analyses_collection()
    result = await collection.insert_one(analysis_data)
    doc_id = str(result.inserted_id)
    logger.info("Analysis saved with id=%s.", doc_id)
    return doc_id


async def get_analysis(analysis_id: str) -> dict[str, Any] | None:
    """
    Retrieve a single analysis by its MongoDB ObjectId string.

    Returns the document dict with ``_id`` converted to ``id``,
    or ``None`` if not found.
    """
    try:
        oid = ObjectId(analysis_id)
    except Exception:
        logger.warning("Invalid ObjectId: %s", analysis_id)
        return None

    collection = get_analyses_collection()
    doc = await collection.find_one({"_id": oid})

    if doc is None:
        return None

    doc["id"] = str(doc.pop("_id"))
    return doc


async def list_analyses() -> list[dict[str, Any]]:
    """
    Return a summary list of all analyses, newest first.

    Each item contains: id, submitted_smiles, canonical_smiles,
    target, disease, overall_recommendation, created_at, patent_count.
    """
    collection = get_analyses_collection()
    cursor = collection.find().sort("created_at", -1)

    results: list[dict[str, Any]] = []
    async for doc in cursor:
        results.append(
            {
                "id": str(doc["_id"]),
                "submitted_smiles": doc.get("submitted_smiles", ""),
                "canonical_smiles": doc.get("canonical_smiles", ""),
                "target": doc.get("target"),
                "disease": doc.get("disease"),
                "overall_recommendation": doc.get("overall_recommendation", ""),
                "created_at": doc.get("created_at", ""),
                "patent_count": len(doc.get("patents", [])),
            }
        )

    logger.info("Listed %d analysis record(s).", len(results))
    return results
