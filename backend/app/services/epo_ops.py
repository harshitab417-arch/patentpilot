"""
PatentPilot EPO OPS Client.

Queries the European Patent Office Open Patent Services (OPS) REST API
for bibliographic data and legal-status information. Uses OAuth2 client
credentials for authentication.
"""

import asyncio
import base64
from html import unescape
import logging
import re
import time
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

# XML namespaces used in EPO OPS responses
_NS = {
    "ops": "http://ops.epo.org",
    "ex": "http://www.epo.org/exchange",
}

_PATENT_ID_CLEAN_RE = re.compile(r"[^A-Z0-9]")
_KIND_SUFFIX_RE = re.compile(r"([A-Z]\d?)$")


class _GooglePatentAbstractParser(HTMLParser):
    """Extract the first usable abstract text from a Google Patents page."""

    def __init__(self) -> None:
        super().__init__()
        self._capture_depth = 0
        self._current_chunks: list[str] = []
        self.abstract: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {key.lower(): value for key, value in attrs}
        class_name = (attr_map.get("class") or "").lower()
        itemprop = (attr_map.get("itemprop") or "").lower()

        if self.abstract is None and (
            itemprop == "abstract" or "abstract" in class_name
        ):
            self._capture_depth = 1
            self._current_chunks = []
            return

        if self._capture_depth > 0:
            self._capture_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if self._capture_depth <= 0:
            return

        self._capture_depth -= 1
        if self._capture_depth == 0 and self.abstract is None:
            text = " ".join(" ".join(self._current_chunks).split())
            if text:
                self.abstract = unescape(text)
            self._current_chunks = []

    def handle_data(self, data: str) -> None:
        if self._capture_depth > 0:
            self._current_chunks.append(data)

    @staticmethod
    def parse_meta_description(html_text: str) -> str | None:
        """Return the best meta-description fallback if present."""
        patterns = (
            r'<meta[^>]+name=["\']DC\.description["\'][^>]+content=["\']([^"\']+)["\']',
            r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)["\']',
            r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\']([^"\']+)["\']',
        )
        for pattern in patterns:
            match = re.search(pattern, html_text, flags=re.I)
            if match and match.group(1).strip():
                return unescape(" ".join(match.group(1).split()))
        return None

    @classmethod
    def parse(cls, html_text: str) -> str | None:
        """Extract a readable abstract from the Google Patents HTML."""
        meta_description = cls.parse_meta_description(html_text)
        if meta_description:
            return meta_description

        parser = cls()
        parser.feed(html_text)
        if parser.abstract:
            return parser.abstract
        return None


class EPOOPSClient:
    """Async client for the EPO Open Patent Services REST API."""

    def __init__(
        self,
        consumer_key: str | None = None,
        consumer_secret: str | None = None,
        base_url: str | None = None,
        auth_url: str | None = None,
    ) -> None:
        self.consumer_key = consumer_key or settings.EPO_CONSUMER_KEY
        self.consumer_secret = consumer_secret or settings.EPO_CONSUMER_SECRET
        self.base_url = (base_url or settings.EPO_OPS_BASE_URL).rstrip("/")
        self.auth_url = auth_url or settings.EPO_OPS_AUTH_URL

        self._access_token: str | None = None
        self._token_expires_at: float = 0.0

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    @property
    def _credentials_configured(self) -> bool:
        return bool(self.consumer_key and self.consumer_secret)

    @staticmethod
    def _publication_components(patent_id: str) -> dict[str, str] | None:
        """
        Split a publication number into EPO docdb parts.

        Accepts common SureChEMBL-style values such as:
        - US20230012345A1
        - EP3456789A1
        - US-1234567-A1
        """
        cleaned = _PATENT_ID_CLEAN_RE.sub("", patent_id.upper().strip())
        if len(cleaned) < 4:
            return None

        country = cleaned[:2]
        if not country.isalpha():
            return None

        remainder = cleaned[2:]
        if not remainder:
            return None

        kind = ""
        kind_match = _KIND_SUFFIX_RE.search(remainder)
        if kind_match:
            candidate_kind = kind_match.group(1)
            candidate_doc = remainder[: -len(candidate_kind)]
            if candidate_doc:
                kind = candidate_kind
                remainder = candidate_doc

        if not remainder or not kind:
            return None

        return {
            "country": country,
            "doc_number": remainder,
            "kind": kind,
            "publication_number": f"{country}{remainder}{kind}",
        }

    def _build_docdb_url(self, patent_id: str, resource: str) -> str | None:
        parts = self._publication_components(patent_id)
        if not parts:
            return None

        return (
            f"{self.base_url}/published-data/publication/docdb/"
            f"{parts['country']}/{parts['doc_number']}/{parts['kind']}/{resource}"
        )

    def _build_legal_url(self, patent_id: str) -> str | None:
        parts = self._publication_components(patent_id)
        if not parts:
            return None

        return (
            f"{self.base_url}/legal/publication/docdb/"
            f"{parts['country']}/{parts['doc_number']}/{parts['kind']}"
        )

    async def _authenticate(self) -> None:
        """Obtain or refresh the OAuth2 access token."""
        if not self._credentials_configured:
            logger.warning("EPO OPS credentials not configured — skipping auth.")
            return

        credentials = base64.b64encode(
            f"{self.consumer_key}:{self.consumer_secret}".encode()
        ).decode()

        headers = {
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    self.auth_url,
                    headers=headers,
                    data="grant_type=client_credentials",
                )
                response.raise_for_status()
                data = response.json()

            self._access_token = data["access_token"]
            expires_in = int(data.get("expires_in", 1200))
            # Refresh 60 s before actual expiry
            self._token_expires_at = time.time() + expires_in - 60
            logger.info("EPO OPS access token acquired (expires in %ds).", expires_in)
        except Exception as exc:
            logger.error("EPO OPS authentication failed: %s", exc)
            self._access_token = None

    async def _get_headers(self) -> dict[str, str]:
        """Return request headers with a valid Bearer token."""
        if (
            self._access_token is None
            or time.time() >= self._token_expires_at
        ):
            await self._authenticate()

        headers: dict[str, str] = {"Accept": "application/xml"}
        if self._access_token:
            headers["Authorization"] = f"Bearer {self._access_token}"
        return headers

    # ------------------------------------------------------------------
    # Retry helper for 403 throttling
    # ------------------------------------------------------------------

    async def _request_with_retry(
        self,
        method: str,
        url: str,
        *,
        max_retries: int = 3,
    ) -> httpx.Response:
        """
        Execute an HTTP request with exponential back-off on 403/429.
        """
        headers = await self._get_headers()
        for attempt in range(max_retries):
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.request(method, url, headers=headers)

            if resp.status_code not in (403, 429):
                resp.raise_for_status()
                return resp

            wait = 2 ** (attempt + 1)
            logger.warning(
                "EPO OPS throttled (%d) on %s — retrying in %ds (attempt %d/%d).",
                resp.status_code,
                url,
                wait,
                attempt + 1,
                max_retries,
            )
            await asyncio.sleep(wait)

        # Final attempt failed
        resp.raise_for_status()
        return resp  # unreachable but keeps type-checker happy

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def get_patent_biblio(self, patent_id: str) -> dict[str, Any]:
        """
        Fetch bibliographic data for *patent_id* from EPO OPS.

        Returns dict with keys: title, abstract, assignee, pub_date.
        Missing fields are ``None``.
        """
        if not self._credentials_configured:
            logger.info(
                "EPO OPS credentials not set - using Google Patents fallback for %s.",
                patent_id,
            )
            scraped_abstract = await self.get_google_patent_abstract(patent_id)
            return {
                "title": None,
                "abstract": scraped_abstract,
                "assignee": None,
                "pub_date": None,
            }

        url = self._build_docdb_url(patent_id, "biblio")

        if not url:
            logger.warning("Could not parse patent id %s into docdb parts.", patent_id)
            scraped_abstract = await self.get_google_patent_abstract(patent_id)
            return {
                "title": None,
                "abstract": scraped_abstract,
                "assignee": None,
                "pub_date": None,
            }

        try:
            resp = await self._request_with_retry("GET", url)
            result = self._parse_biblio_xml(resp.text)
            if result.get("abstract"):
                return result

            abstract_url = self._build_docdb_url(patent_id, "abstract")
            if abstract_url:
                try:
                    abstract_resp = await self._request_with_retry("GET", abstract_url)
                    scraped_abstract = self._parse_abstract_xml(abstract_resp.text)
                    if scraped_abstract:
                        result["abstract"] = scraped_abstract
                except Exception as exc:
                    logger.debug(
                        "EPO OPS abstract fetch failed for %s: %s", patent_id, exc
                    )

            scraped_abstract = await self.get_google_patent_abstract(patent_id)
            if scraped_abstract:
                result["abstract"] = scraped_abstract
            return result
        except Exception as exc:
            logger.error("Failed to fetch biblio for %s: %s", patent_id, exc)
            return {"title": None, "abstract": None, "assignee": None, "pub_date": None}

    async def get_legal_status(self, patent_id: str) -> str | None:
        """
        Determine the legal status of *patent_id*.

        Returns one of 'Active', 'Expired', 'Lapsed', 'Revoked', or None.
        """
        if not self._credentials_configured:
            logger.info(
                "EPO OPS credentials not set — returning no legal status for %s.",
                patent_id,
            )
            return None

        url = self._build_legal_url(patent_id)
        if not url:
            logger.warning("Could not parse patent id %s into docdb parts.", patent_id)
            return None

        try:
            resp = await self._request_with_retry("GET", url)
            return self._parse_legal_status_xml(resp.text)
        except Exception as exc:
            logger.error("Failed to fetch legal status for %s: %s", patent_id, exc)
            return None

    async def get_google_patent_abstract(self, patent_id: str) -> str | None:
        """
        Scrape the abstract from the public Google Patents page.

        This is used as a fallback when EPO OPS does not return an abstract.
        """
        normalized_id = patent_id.replace("-", "").strip()
        if not normalized_id:
            return None

        url = f"https://patents.google.com/patent/{normalized_id}/en"
        headers = {
            "Accept": "text/html,application/xhtml+xml",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
            ),
        }

        try:
            async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
                resp = await client.get(url, headers=headers)
                resp.raise_for_status()
            abstract = _GooglePatentAbstractParser.parse(resp.text)
            if abstract:
                logger.info("Google Patents abstract scraped for %s.", patent_id)
            return abstract
        except Exception as exc:
            logger.debug("Google Patents scrape failed for %s: %s", patent_id, exc)
            return None

    @staticmethod
    def _parse_abstract_xml(xml_text: str) -> str | None:
        """Extract the abstract text from an OPS abstract response."""
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as exc:
            logger.error("XML parse error in abstract response: %s", exc)
            return None

        abstract_nodes = root.findall(".//ex:abstract[@lang='en']/ex:p", _NS)
        abstract_text = " ".join(
            " ".join(node.itertext()).strip()
            for node in abstract_nodes
            if " ".join(node.itertext()).strip()
        )
        if abstract_text:
            return " ".join(abstract_text.split())
        return None

    # ------------------------------------------------------------------
    # XML parsing helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_biblio_xml(xml_text: str) -> dict[str, Any]:
        """Extract bibliographic fields from an EPO OPS XML response."""
        result: dict[str, Any] = {
            "title": None,
            "abstract": None,
            "assignee": None,
            "pub_date": None,
        }

        try:
            root = ET.fromstring(xml_text)

            # Title (English)
            title_el = root.find(".//ex:invention-title[@lang='en']", _NS)
            if title_el is not None and title_el.text:
                result["title"] = title_el.text.strip()

            # Abstract (English)
            abstract_nodes = root.findall(".//ex:abstract[@lang='en']/ex:p", _NS)
            abstract_text = " ".join(
                " ".join(node.itertext()).strip()
                for node in abstract_nodes
                if " ".join(node.itertext()).strip()
            )
            if abstract_text:
                result["abstract"] = " ".join(abstract_text.split())

            # Assignee
            assignee_el = root.find(
                ".//ex:parties/ex:applicants/"
                "ex:applicant[@data-format='docdb']/"
                "ex:applicant-name/ex:name",
                _NS,
            )
            if assignee_el is not None and assignee_el.text:
                result["assignee"] = assignee_el.text.strip()

            # Publication date
            date_el = root.find(
                ".//ex:publication-reference/"
                "ex:document-id[@document-id-type='docdb']/"
                "ex:date",
                _NS,
            )
            if date_el is not None and date_el.text:
                result["pub_date"] = date_el.text.strip()

        except ET.ParseError as exc:
            logger.error("XML parse error in biblio response: %s", exc)

        return result

    @staticmethod
    def _parse_legal_status_xml(xml_text: str) -> str | None:
        """Determine legal status from an EPO OPS legal-status XML response."""
        try:
            root = ET.fromstring(xml_text)
            text_lower = xml_text.lower()

            # Simple heuristic based on legal-event codes and descriptions
            if "lapsed" in text_lower or "lapse" in text_lower:
                return "Lapsed"
            if "revoked" in text_lower or "revocation" in text_lower:
                return "Revoked"
            if "expired" in text_lower or "expiry" in text_lower:
                return "Expired"
            if "granted" in text_lower or "active" in text_lower:
                return "Active"

            # If we got a valid XML response but couldn't determine status
            if root is not None:
                return "Unknown"
        except ET.ParseError as exc:
            logger.error("XML parse error in legal-status response: %s", exc)

        return None
