"""
Unit tests for the patent enrichment helpers.
"""

from __future__ import annotations

import asyncio

from app.agents.retrieval import retrieve_patents
from app.services.epo_ops import EPOOPSClient, _GooglePatentAbstractParser


def test_parse_biblio_xml_joins_multiple_abstract_paragraphs() -> None:
    xml_text = """
    <ops:world-patent-data xmlns:ops="http://ops.epo.org" xmlns:ex="http://www.epo.org/exchange">
      <ex:abstract lang="en">
        <ex:p>First paragraph.</ex:p>
        <ex:p>Second paragraph with extra detail.</ex:p>
      </ex:abstract>
    </ops:world-patent-data>
    """

    parsed = EPOOPSClient._parse_biblio_xml(xml_text)

    assert parsed["abstract"] == "First paragraph. Second paragraph with extra detail."


def test_google_patent_parser_prefers_meta_description() -> None:
    html_text = """
    <html>
      <head>
        <meta name="DC.description" content="A compact abstract extracted from the page.">
      </head>
      <body>
        <div class="abstract">This body text should not be needed.</div>
      </body>
    </html>
    """

    assert _GooglePatentAbstractParser.parse(html_text) == (
        "A compact abstract extracted from the page."
    )


def test_publication_components_split_docdb_ids() -> None:
    parts = EPOOPSClient._publication_components("US-1234567-A1")

    assert parts == {
        "country": "US",
        "doc_number": "1234567",
        "kind": "A1",
        "publication_number": "US1234567A1",
    }


def test_parse_abstract_xml_extracts_english_text() -> None:
    xml_text = """
    <ops:world-patent-data xmlns:ops="http://ops.epo.org" xmlns:ex="http://www.epo.org/exchange">
      <ex:abstract lang="en">
        <ex:p>First paragraph.</ex:p>
        <ex:p>Second paragraph with extra detail.</ex:p>
      </ex:abstract>
    </ops:world-patent-data>
    """

    assert EPOOPSClient._parse_abstract_xml(xml_text) == (
        "First paragraph. Second paragraph with extra detail."
    )


def test_retrieve_patents_uses_google_patent_fallback() -> None:
    class FakeSureChEMBLClient:
        async def search_by_similarity(self, canonical_smiles: str, threshold: float = 0.7):
            return [
                {
                    "patent_id": "US-1234567-A1",
                    "title": "SureChEMBL title",
                    "similarity_score": 0.82,
                    "source": "SureChEMBL",
                }
            ]

    class FakeEPOClient:
        async def get_patent_biblio(self, patent_id: str):
            return {"title": None, "abstract": None, "assignee": None, "pub_date": None}

        async def get_legal_status(self, patent_id: str):
            return "Active"

        async def get_google_patent_abstract(self, patent_id: str):
            return "Google Patents fallback abstract."

    patents = asyncio.run(
        retrieve_patents(
            canonical_smiles="CC(=O)Oc1ccccc1C(=O)O",
            target="kinase",
            disease="cancer",
            surechembl_client=FakeSureChEMBLClient(),
            epo_client=FakeEPOClient(),
        )
    )

    assert len(patents) == 1
    patent = patents[0]
    assert patent["abstract"] == "Google Patents fallback abstract."
    assert patent["abstract_summary"] == "Google Patents fallback abstract."
    assert patent["patent_url"] == "https://patents.google.com/patent/US1234567A1/en"
