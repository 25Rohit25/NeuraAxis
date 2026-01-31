"""
NEURAXIS - PubMed API Client
Client for NCBI E-utilities API to search medical literature
"""

import asyncio
import hashlib
import logging
import time
from datetime import datetime
from typing import Any
from xml.etree import ElementTree

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.agents.research_schemas import (
    Author,
    Document,
    EvidenceGrade,
    SourceType,
    StudyType,
)
from app.core.config import settings

logger = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

PUBMED_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
PUBMED_SEARCH_URL = f"{PUBMED_BASE_URL}/esearch.fcgi"
PUBMED_FETCH_URL = f"{PUBMED_BASE_URL}/efetch.fcgi"
PUBMED_SUMMARY_URL = f"{PUBMED_BASE_URL}/esummary.fcgi"

# Rate limiting: NCBI allows 3 requests/second without API key, 10/second with key
RATE_LIMIT_DELAY = 0.1  # 100ms between requests


# Study type mapping from PubMed publication types
STUDY_TYPE_MAP = {
    "Meta-Analysis": StudyType.META_ANALYSIS,
    "Systematic Review": StudyType.SYSTEMATIC_REVIEW,
    "Randomized Controlled Trial": StudyType.RCT,
    "Clinical Trial": StudyType.RCT,
    "Cohort Studies": StudyType.COHORT,
    "Case-Control Studies": StudyType.CASE_CONTROL,
    "Case Reports": StudyType.CASE_REPORT,
    "Review": StudyType.REVIEW,
    "Practice Guideline": StudyType.GUIDELINE,
    "Guideline": StudyType.GUIDELINE,
}


# =============================================================================
# PubMed Client
# =============================================================================


class PubMedClient:
    """
    Client for searching PubMed via NCBI E-utilities API.

    Features:
    - Search with boolean queries
    - Fetch article details and abstracts
    - Rate limiting to respect API limits
    - Retry logic for resilience
    - Response caching
    """

    def __init__(
        self,
        api_key: str | None = None,
        email: str | None = None,
        timeout: float = 30.0,
    ):
        """
        Initialize PubMed client.

        Args:
            api_key: NCBI API key for higher rate limits
            email: Contact email (required by NCBI)
            timeout: Request timeout in seconds
        """
        self.api_key = api_key or getattr(settings, "NCBI_API_KEY", None)
        self.email = email or getattr(settings, "NCBI_EMAIL", "neuraxis@example.com")
        self.timeout = timeout

        self._client = httpx.AsyncClient(timeout=timeout)
        self._last_request_time = 0
        self._cache: dict[str, Any] = {}

        logger.info("PubMed client initialized")

    async def _rate_limit(self):
        """Enforce rate limiting between requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < RATE_LIMIT_DELAY:
            await asyncio.sleep(RATE_LIMIT_DELAY - elapsed)
        self._last_request_time = time.time()

    def _get_cache_key(self, prefix: str, params: dict) -> str:
        """Generate cache key from parameters."""
        param_str = str(sorted(params.items()))
        return f"{prefix}:{hashlib.md5(param_str.encode()).hexdigest()}"

    def _base_params(self) -> dict:
        """Get base parameters for all requests."""
        params = {"email": self.email}
        if self.api_key:
            params["api_key"] = self.api_key
        return params

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def search(
        self,
        query: str,
        max_results: int = 10,
        date_range_years: int | None = 5,
        sort: str = "relevance",
    ) -> list[str]:
        """
        Search PubMed for articles matching query.

        Args:
            query: Search query (supports boolean operators)
            max_results: Maximum number of PMIDs to return
            date_range_years: Limit to recent years
            sort: Sort order (relevance, pub_date)

        Returns:
            List of PubMed IDs (PMIDs)
        """
        await self._rate_limit()

        params = {
            **self._base_params(),
            "db": "pubmed",
            "term": query,
            "retmax": max_results,
            "retmode": "json",
            "sort": sort,
        }

        # Add date filter
        if date_range_years:
            min_date = datetime.now().year - date_range_years
            params["mindate"] = f"{min_date}/01/01"
            params["maxdate"] = "3000"  # Future date for "until now"
            params["datetype"] = "pdat"  # Publication date

        # Check cache
        cache_key = self._get_cache_key("search", params)
        if cache_key in self._cache:
            logger.debug(f"Cache hit for search: {query[:50]}...")
            return self._cache[cache_key]

        try:
            response = await self._client.get(PUBMED_SEARCH_URL, params=params)
            response.raise_for_status()

            data = response.json()
            pmids = data.get("esearchresult", {}).get("idlist", [])

            # Cache result
            self._cache[cache_key] = pmids

            logger.info(f"PubMed search returned {len(pmids)} results for: {query[:50]}...")
            return pmids

        except Exception as e:
            logger.error(f"PubMed search failed: {e}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def fetch_articles(self, pmids: list[str]) -> list[Document]:
        """
        Fetch full article details for given PMIDs.

        Args:
            pmids: List of PubMed IDs

        Returns:
            List of Document objects
        """
        if not pmids:
            return []

        await self._rate_limit()

        params = {
            **self._base_params(),
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "xml",
            "rettype": "abstract",
        }

        try:
            response = await self._client.get(PUBMED_FETCH_URL, params=params)
            response.raise_for_status()

            documents = self._parse_pubmed_xml(response.text)

            logger.info(f"Fetched {len(documents)} articles from PubMed")
            return documents

        except Exception as e:
            logger.error(f"PubMed fetch failed: {e}")
            raise

    def _parse_pubmed_xml(self, xml_text: str) -> list[Document]:
        """Parse PubMed XML response into Document objects."""
        documents = []

        try:
            root = ElementTree.fromstring(xml_text)

            for article in root.findall(".//PubmedArticle"):
                try:
                    doc = self._parse_article(article)
                    if doc:
                        documents.append(doc)
                except Exception as e:
                    logger.warning(f"Failed to parse article: {e}")
                    continue

        except ElementTree.ParseError as e:
            logger.error(f"XML parse error: {e}")

        return documents

    def _parse_article(self, article: ElementTree.Element) -> Document | None:
        """Parse single article element."""
        medline = article.find(".//MedlineCitation")
        if medline is None:
            return None

        pmid_elem = medline.find("PMID")
        pmid = pmid_elem.text if pmid_elem is not None else None
        if not pmid:
            return None

        # Get article info
        article_elem = medline.find("Article")
        if article_elem is None:
            return None

        # Title
        title_elem = article_elem.find("ArticleTitle")
        title = title_elem.text if title_elem is not None else "Untitled"

        # Abstract
        abstract_elem = article_elem.find(".//Abstract/AbstractText")
        abstract = ""
        if abstract_elem is not None:
            abstract = abstract_elem.text or ""
        else:
            # Try multiple abstract sections
            abstract_parts = []
            for abs_text in article_elem.findall(".//Abstract/AbstractText"):
                label = abs_text.get("Label", "")
                text = abs_text.text or ""
                if label:
                    abstract_parts.append(f"{label}: {text}")
                else:
                    abstract_parts.append(text)
            abstract = " ".join(abstract_parts)

        # Authors
        authors = []
        for author in article_elem.findall(".//AuthorList/Author"):
            last_name = author.findtext("LastName", "")
            fore_name = author.findtext("ForeName", "")
            if last_name:
                name = f"{last_name} {fore_name}".strip()
                affiliation = author.findtext(".//Affiliation", "")
                authors.append(Author(name=name, affiliation=affiliation or None))

        # Journal
        journal_elem = article_elem.find(".//Journal/Title")
        journal = journal_elem.text if journal_elem is not None else None

        # Publication date
        pub_date = None
        date_elem = article_elem.find(".//PubDate")
        if date_elem is not None:
            year = date_elem.findtext("Year")
            month = date_elem.findtext("Month", "01")
            day = date_elem.findtext("Day", "01")
            if year:
                try:
                    # Handle month as name or number
                    month_map = {
                        "Jan": 1,
                        "Feb": 2,
                        "Mar": 3,
                        "Apr": 4,
                        "May": 5,
                        "Jun": 6,
                        "Jul": 7,
                        "Aug": 8,
                        "Sep": 9,
                        "Oct": 10,
                        "Nov": 11,
                        "Dec": 12,
                    }
                    if month in month_map:
                        month = str(month_map[month])
                    pub_date = datetime(int(year), int(month), int(day))
                except (ValueError, TypeError):
                    try:
                        pub_date = datetime(int(year), 1, 1)
                    except (ValueError, TypeError):
                        pass

        # DOI
        doi = None
        for id_elem in article_elem.findall(".//ELocationID"):
            if id_elem.get("EIdType") == "doi":
                doi = id_elem.text
                break

        # MeSH terms
        mesh_terms = []
        for mesh in medline.findall(".//MeshHeading/DescriptorName"):
            if mesh.text:
                mesh_terms.append(mesh.text)

        # Keywords
        keywords = []
        for kw in medline.findall(".//KeywordList/Keyword"):
            if kw.text:
                keywords.append(kw.text)

        # Publication types for study classification
        pub_types = []
        for pt in article_elem.findall(".//PublicationTypeList/PublicationType"):
            if pt.text:
                pub_types.append(pt.text)

        study_type = self._classify_study_type(pub_types)
        evidence_grade = self._grade_evidence(study_type)

        return Document(
            id=f"pubmed:{pmid}",
            source_type=SourceType.PUBMED,
            title=title,
            abstract=abstract,
            content=abstract,  # Use abstract as content
            authors=authors,
            publication_date=pub_date,
            journal=journal,
            doi=doi,
            pmid=pmid,
            study_type=study_type,
            evidence_grade=evidence_grade,
            keywords=keywords,
            mesh_terms=mesh_terms,
        )

    def _classify_study_type(self, pub_types: list[str]) -> StudyType:
        """Classify study type from publication types."""
        for pt in pub_types:
            if pt in STUDY_TYPE_MAP:
                return STUDY_TYPE_MAP[pt]
        return StudyType.OTHER

    def _grade_evidence(self, study_type: StudyType) -> EvidenceGrade:
        """Assign evidence grade based on study type."""
        grade_a = {
            StudyType.META_ANALYSIS,
            StudyType.SYSTEMATIC_REVIEW,
            StudyType.RCT,
        }
        grade_b = {
            StudyType.COHORT,
            StudyType.CASE_CONTROL,
        }

        if study_type in grade_a:
            return EvidenceGrade.A
        elif study_type in grade_b:
            return EvidenceGrade.B
        else:
            return EvidenceGrade.C

    async def search_and_fetch(
        self,
        query: str,
        max_results: int = 10,
        date_range_years: int | None = 5,
    ) -> list[Document]:
        """
        Combined search and fetch operation.

        Args:
            query: Search query
            max_results: Maximum results
            date_range_years: Date range filter

        Returns:
            List of Document objects
        """
        pmids = await self.search(
            query=query,
            max_results=max_results,
            date_range_years=date_range_years,
        )

        if not pmids:
            return []

        return await self.fetch_articles(pmids)

    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()


# =============================================================================
# Clinical Trials Client
# =============================================================================

CLINICAL_TRIALS_API = "https://clinicaltrials.gov/api/v2"


class ClinicalTrialsClient:
    """
    Client for ClinicalTrials.gov API.
    """

    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout
        self._client = httpx.AsyncClient(timeout=timeout)
        self._last_request_time = 0

    async def _rate_limit(self):
        """Rate limiting for API."""
        elapsed = time.time() - self._last_request_time
        if elapsed < 0.5:  # 2 requests per second
            await asyncio.sleep(0.5 - elapsed)
        self._last_request_time = time.time()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def search(
        self,
        query: str,
        max_results: int = 10,
        status: list[str] | None = None,
    ) -> list[dict]:
        """
        Search for clinical trials.

        Args:
            query: Search query
            max_results: Maximum results
            status: Filter by status (RECRUITING, COMPLETED, etc.)

        Returns:
            List of trial data dictionaries
        """
        await self._rate_limit()

        params = {
            "query.term": query,
            "pageSize": max_results,
            "format": "json",
        }

        if status:
            params["filter.overallStatus"] = ",".join(status)

        try:
            response = await self._client.get(
                f"{CLINICAL_TRIALS_API}/studies",
                params=params,
            )
            response.raise_for_status()

            data = response.json()
            studies = data.get("studies", [])

            logger.info(f"ClinicalTrials search returned {len(studies)} results")
            return studies

        except Exception as e:
            logger.error(f"ClinicalTrials search failed: {e}")
            return []

    def parse_trial(self, trial_data: dict) -> dict:
        """Parse trial data into structured format."""
        protocol = trial_data.get("protocolSection", {})

        id_module = protocol.get("identificationModule", {})
        status_module = protocol.get("statusModule", {})
        desc_module = protocol.get("descriptionModule", {})
        conditions_module = protocol.get("conditionsModule", {})
        interventions_module = protocol.get("armsInterventionsModule", {})
        sponsor_module = protocol.get("sponsorCollaboratorsModule", {})
        design_module = protocol.get("designModule", {})

        # Parse status
        status_str = status_module.get("overallStatus", "UNKNOWN").upper()
        status_map = {
            "RECRUITING": "recruiting",
            "ACTIVE_NOT_RECRUITING": "active",
            "COMPLETED": "completed",
            "TERMINATED": "terminated",
            "SUSPENDED": "suspended",
            "WITHDRAWN": "withdrawn",
        }
        status = status_map.get(status_str, "unknown")

        # Parse dates
        start_date = None
        completion_date = None
        try:
            start_str = status_module.get("startDateStruct", {}).get("date")
            if start_str:
                start_date = datetime.strptime(start_str, "%Y-%m-%d")
        except (ValueError, TypeError):
            pass

        try:
            comp_str = status_module.get("completionDateStruct", {}).get("date")
            if comp_str:
                completion_date = datetime.strptime(comp_str, "%Y-%m-%d")
        except (ValueError, TypeError):
            pass

        # Get interventions
        interventions = []
        for intervention in interventions_module.get("interventions", []):
            name = intervention.get("name", "")
            int_type = intervention.get("type", "")
            if name:
                interventions.append(f"{int_type}: {name}" if int_type else name)

        return {
            "nct_id": id_module.get("nctId", ""),
            "title": id_module.get("briefTitle", ""),
            "status": status,
            "phase": ",".join(design_module.get("phases", [])),
            "conditions": conditions_module.get("conditions", []),
            "interventions": interventions,
            "sponsor": sponsor_module.get("leadSponsor", {}).get("name"),
            "start_date": start_date,
            "completion_date": completion_date,
            "enrollment": design_module.get("enrollmentInfo", {}).get("count"),
            "summary": desc_module.get("briefSummary"),
            "url": f"https://clinicaltrials.gov/study/{id_module.get('nctId', '')}",
        }

    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()


# =============================================================================
# Factory Functions
# =============================================================================


def create_pubmed_client() -> PubMedClient:
    """Create configured PubMed client."""
    return PubMedClient()


def create_clinical_trials_client() -> ClinicalTrialsClient:
    """Create configured ClinicalTrials client."""
    return ClinicalTrialsClient()
