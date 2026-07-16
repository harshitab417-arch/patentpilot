"""
Standalone Gemini validator.

Run from anywhere to confirm:
  - backend/.env is loaded
  - GEMINI_API_KEY exists
  - the configured model is used
  - the Gemini SDK can return strict JSON for the evidence path

This uses a synthetic patent payload so it does not depend on a live
MongoDB analysis record.
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app.config import settings
from app.services.gemini_service import GeminiService


SYNTHETIC_PATENT = {
    "patent_id": "SYNTHETIC-VALIDATION-001",
    "title": "Solid oral formulation of kinase inhibitor for cancer therapy",
    "abstract": (
        "The invention relates to a solid oral dosage form, pharmaceutical "
        "formulation, and method of treating oncology indications with a "
        "kinase inhibitor scaffold."
    ),
    "abstract_summary": "Solid oral dosage form for cancer therapy.",
    "legal_status": "Not available",
}

SYNTHETIC_MOLECULE = {
    "smiles": "CC(C)Cc1ccc(C(C)C(=O)O)cc1",
    "target": "kinase",
    "disease": "cancer",
}


async def main() -> None:
    print(
        json.dumps(
            {
                "env_file": str(BACKEND_DIR / ".env"),
                "key_present": bool(settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.strip()),
                "key_length": len(settings.GEMINI_API_KEY or ""),
                "model": settings.GEMINI_MODEL,
            },
            indent=2,
        )
    )

    service = GeminiService()
    evidence = await service.extract_patent_evidence(
        SYNTHETIC_PATENT,
        SYNTHETIC_MOLECULE,
    )
    print(json.dumps(evidence, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
