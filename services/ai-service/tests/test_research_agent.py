"""
NEURAXIS - Research Agent Unit Tests
Tests with mock API responses
"""

import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.agents.research import (
    CitationFormatter,
    ContradictionDetector,
    QueryExpander,
    ReRanker,
    ResearchAgent,
    ResearchSynthesizer,
    create_research_agent,
)
from app.agents.research_schemas import (
    Author,
    Citation,
    ClinicalTrial,
    Document,
    EvidenceGrade,
    ExpandedQuery,
    MedicalConcept,
    ResearchQuery,
    ResearchRequest,
    ResearchResponse,
    SourceType,
    StudyType,
    TrialStatus,
)
from app.services.pubmed import ClinicalTrialsClient, PubMedClient

# =============================================================================
# Mock Data
# =============================================================================

MOCK_DOCUMENTS = [
    Document(
        id="pubmed:12345678",
        source_type=SourceType.PUBMED,
        title="Efficacy of Drug X in Treating Hypertension: A Randomized Controlled Trial",
        abstract="Background: Hypertension affects millions worldwide. Methods: We conducted a double-blind RCT with 500 patients...",
        authors=[
            Author(name="Smith J", affiliation="Harvard Medical School"),
            Author(name="Johnson M", affiliation="MIT"),
        ],
        publication_date=datetime(2023, 6, 15),
        journal="New England Journal of Medicine",
        doi="10.1056/NEJMoa2023456",
        pmid="12345678",
        study_type=StudyType.RCT,
        evidence_grade=EvidenceGrade.A,
        mesh_terms=["Hypertension", "Antihypertensive Agents"],
        relevance_score=0.95,
    ),
    Document(
        id="pubmed:87654321",
        source_type=SourceType.PUBMED,
        title="Meta-analysis of Blood Pressure Medications",
        abstract="We performed a systematic review and meta-analysis of 50 RCTs...",
        authors=[Author(name="Williams R")],
        publication_date=datetime(2022, 3, 20),
        journal="JAMA",
        pmid="87654321",
        study_type=StudyType.META_ANALYSIS,
        evidence_grade=EvidenceGrade.A,
        relevance_score=0.88,
    ),
    Document(
        id="pubmed:11111111",
        source_type=SourceType.PUBMED,
        title="Case Report: Unusual Response to Antihypertensive Therapy",
        abstract="We present a 65-year-old patient with resistant hypertension...",
        authors=[Author(name="Brown K")],
        publication_date=datetime(2021, 1, 5),
        journal="Case Reports in Medicine",
        pmid="11111111",
        study_type=StudyType.CASE_REPORT,
        evidence_grade=EvidenceGrade.C,
        relevance_score=0.65,
    ),
]

MOCK_CLINICAL_TRIAL = ClinicalTrial(
    nct_id="NCT04123456",
    title="Study of Novel Antihypertensive Agent",
    status=TrialStatus.RECRUITING,
    phase="Phase 3",
    conditions=["Hypertension"],
    interventions=["Drug: Novel Agent X"],
    sponsor="Pharma Corp",
    enrollment=1000,
    url="https://clinicaltrials.gov/study/NCT04123456",
)

MOCK_EXPANDED_QUERY = {
    "medical_concepts": [
        {
            "term": "hypertension",
            "concept_type": "disease",
            "synonyms": ["high blood pressure", "HTN", "elevated blood pressure"],
            "mesh_id": "D006973",
        },
        {
            "term": "treatment",
            "concept_type": "procedure",
            "synonyms": ["therapy", "management"],
        },
    ],
    "expanded_terms": ["antihypertensive", "blood pressure control", "cardiovascular"],
    "boolean_query": "(hypertension OR high blood pressure) AND (treatment OR therapy)",
}


# =============================================================================
# Query Expander Tests
# =============================================================================


class TestQueryExpander:
    """Tests for QueryExpander."""

    @pytest.mark.asyncio
    async def test_expand_query(self):
        """Test query expansion."""
        with patch("app.agents.research.ChatOpenAI") as mock_llm:
            mock_response = MagicMock()
            mock_response.content = json.dumps(MOCK_EXPANDED_QUERY)

            mock_chain = AsyncMock(return_value=mock_response)
            mock_llm.return_value.__or__ = MagicMock(return_value=mock_chain)

            expander = QueryExpander(llm=mock_llm.return_value)

            # Mock the chain
            expander.prompt = MagicMock()
            expander.prompt.__or__ = MagicMock(return_value=mock_chain)

            result = await expander.expand_query("hypertension treatment")

            assert result.original_query == "hypertension treatment"

    def test_expanded_query_model(self):
        """Test ExpandedQuery model."""
        expanded = ExpandedQuery(
            original_query="test query",
            medical_concepts=[
                MedicalConcept(
                    term="diabetes",
                    concept_type="disease",
                    synonyms=["DM"],
                )
            ],
            expanded_terms=["insulin", "glucose"],
            boolean_query="diabetes OR DM",
        )

        assert expanded.original_query == "test query"
        assert len(expanded.medical_concepts) == 1
        assert expanded.medical_concepts[0].term == "diabetes"


# =============================================================================
# ReRanker Tests
# =============================================================================


class TestReRanker:
    """Tests for ReRanker with RRF."""

    def test_rerank_by_combined_score(self):
        """Test that reranking combines relevance and recency."""
        reranker = ReRanker()

        documents = [doc.model_copy() for doc in MOCK_DOCUMENTS]

        reranked = reranker.rerank(documents, "hypertension treatment")

        # Should be reordered by combined score
        assert len(reranked) == 3

        # Scores should be set
        for doc in reranked:
            assert doc.combined_score > 0
            assert doc.recency_score > 0

    def test_recency_scoring(self):
        """Test recency score calculation."""
        reranker = ReRanker()

        # Most recent document should have highest recency score
        documents = [doc.model_copy() for doc in MOCK_DOCUMENTS]
        reranked = reranker.rerank(documents, "test")

        # First doc is newest (2023)
        newest = [d for d in reranked if d.pmid == "12345678"][0]
        oldest = [d for d in reranked if d.pmid == "11111111"][0]

        assert newest.recency_score > oldest.recency_score

    def test_deduplicate(self):
        """Test document deduplication."""
        reranker = ReRanker()

        documents = [
            Document(
                id="1",
                source_type=SourceType.PUBMED,
                title="Hypertension Treatment Study Results",
                relevance_score=0.9,
            ),
            Document(
                id="2",
                source_type=SourceType.PUBMED,
                title="Hypertension Treatment Study Results Updated",  # Very similar
                relevance_score=0.8,
            ),
            Document(
                id="3",
                source_type=SourceType.PUBMED,
                title="Completely Different Study on Cancer",
                relevance_score=0.7,
            ),
        ]

        deduped = reranker.deduplicate(documents, similarity_threshold=0.7)

        # Should remove duplicate
        assert len(deduped) == 2

    def test_empty_documents(self):
        """Test with empty document list."""
        reranker = ReRanker()

        assert reranker.rerank([], "test") == []
        assert reranker.deduplicate([]) == []


# =============================================================================
# Citation Formatter Tests
# =============================================================================


class TestCitationFormatter:
    """Tests for AMA citation formatting."""

    def test_format_ama_complete(self):
        """Test complete AMA citation."""
        formatter = CitationFormatter()

        doc = MOCK_DOCUMENTS[0]
        citation = formatter.format_ama(doc)

        assert "Smith J" in citation
        assert "Johnson M" in citation
        assert "Efficacy of Drug X" in citation
        assert "New England Journal of Medicine" in citation
        assert "10.1056/NEJMoa2023456" in citation

    def test_format_ama_minimal(self):
        """Test AMA citation with minimal data."""
        formatter = CitationFormatter()

        doc = Document(
            id="test",
            source_type=SourceType.PUBMED,
            title="Test Article",
            pmid="12345",
        )

        citation = formatter.format_ama(doc)

        assert "Test Article" in citation
        assert "PMID: 12345" in citation

    def test_create_citation_object(self):
        """Test creating Citation object."""
        formatter = CitationFormatter()

        doc = MOCK_DOCUMENTS[0]
        citation = formatter.create_citation(doc)

        assert isinstance(citation, Citation)
        assert citation.source_id == doc.id
        assert citation.pmid == doc.pmid
        assert citation.doi == doc.doi
        assert "pubmed.ncbi.nlm.nih.gov" in citation.url

    def test_many_authors(self):
        """Test citation with more than 6 authors."""
        formatter = CitationFormatter()

        doc = Document(
            id="test",
            source_type=SourceType.PUBMED,
            title="Multi-Author Study",
            authors=[Author(name=f"Author{i}") for i in range(10)],
        )

        citation = formatter.format_ama(doc)

        assert "et al" in citation


# =============================================================================
# PubMed Client Tests
# =============================================================================


class TestPubMedClient:
    """Tests for PubMed API client."""

    @pytest.mark.asyncio
    async def test_search(self):
        """Test PubMed search."""
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "esearchresult": {"idlist": ["12345678", "87654321"]}
            }
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            client = PubMedClient()
            client._client = MagicMock()
            client._client.get = AsyncMock(return_value=mock_response)

            pmids = await client.search("hypertension", max_results=10)

            assert len(pmids) == 2
            assert "12345678" in pmids

    def test_study_type_classification(self):
        """Test study type classification from publication types."""
        client = PubMedClient()

        assert client._classify_study_type(["Meta-Analysis"]) == StudyType.META_ANALYSIS
        assert client._classify_study_type(["Randomized Controlled Trial"]) == StudyType.RCT
        assert client._classify_study_type(["Case Reports"]) == StudyType.CASE_REPORT
        assert client._classify_study_type(["Unknown"]) == StudyType.OTHER

    def test_evidence_grading(self):
        """Test evidence grade assignment."""
        client = PubMedClient()

        assert client._grade_evidence(StudyType.META_ANALYSIS) == EvidenceGrade.A
        assert client._grade_evidence(StudyType.RCT) == EvidenceGrade.A
        assert client._grade_evidence(StudyType.COHORT) == EvidenceGrade.B
        assert client._grade_evidence(StudyType.CASE_REPORT) == EvidenceGrade.C


# =============================================================================
# Research Agent Tests
# =============================================================================


class TestResearchAgent:
    """Tests for ResearchAgent."""

    @pytest.fixture
    def mock_agent(self):
        """Create agent with mocked dependencies."""
        with patch.multiple(
            "app.agents.research",
            QueryExpander=MagicMock(),
            PubMedClient=MagicMock(),
            ClinicalTrialsClient=MagicMock(),
            get_embedding_service=MagicMock(),
            get_vector_store=MagicMock(),
        ):
            agent = ResearchAgent()
            agent.redis_client = None
            yield agent

    def test_generate_cache_key(self, mock_agent):
        """Test cache key generation."""
        query1 = ResearchQuery(query="hypertension treatment", max_results=10)
        query2 = ResearchQuery(query="hypertension treatment", max_results=10)
        query3 = ResearchQuery(query="different query", max_results=10)

        key1 = mock_agent._generate_cache_key(query1)
        key2 = mock_agent._generate_cache_key(query2)
        key3 = mock_agent._generate_cache_key(query3)

        assert key1 == key2  # Same query = same key
        assert key1 != key3  # Different query = different key
        assert key1.startswith("research:")

    def test_calculate_overall_grade(self, mock_agent):
        """Test overall evidence grade calculation."""
        # Majority A
        docs_a = [
            Document(
                id="1", source_type=SourceType.PUBMED, title="A", evidence_grade=EvidenceGrade.A
            ),
            Document(
                id="2", source_type=SourceType.PUBMED, title="B", evidence_grade=EvidenceGrade.A
            ),
            Document(
                id="3", source_type=SourceType.PUBMED, title="C", evidence_grade=EvidenceGrade.B
            ),
        ]
        assert mock_agent._calculate_overall_grade(docs_a) == EvidenceGrade.A

        # Majority B
        docs_b = [
            Document(
                id="1", source_type=SourceType.PUBMED, title="A", evidence_grade=EvidenceGrade.B
            ),
            Document(
                id="2", source_type=SourceType.PUBMED, title="B", evidence_grade=EvidenceGrade.B
            ),
            Document(
                id="3", source_type=SourceType.PUBMED, title="C", evidence_grade=EvidenceGrade.C
            ),
        ]
        assert mock_agent._calculate_overall_grade(docs_b) == EvidenceGrade.B

        # Empty list
        assert mock_agent._calculate_overall_grade([]) is None

    def test_calculate_confidence(self, mock_agent):
        """Test confidence score calculation."""
        from app.agents.research_schemas import KeyFinding, ResearchSynthesis

        docs = MOCK_DOCUMENTS
        synthesis = ResearchSynthesis(
            summary="Test summary",
            key_findings=[
                KeyFinding(
                    finding="Finding 1",
                    source_ids=["1"],
                    evidence_grade=EvidenceGrade.A,
                    confidence=0.9,
                ),
                KeyFinding(
                    finding="Finding 2",
                    source_ids=["2"],
                    evidence_grade=EvidenceGrade.B,
                    confidence=0.7,
                ),
            ],
        )

        confidence = mock_agent._calculate_confidence(docs, synthesis)

        assert 0 <= confidence <= 1
        assert confidence > 0.3  # Should be reasonable confidence with good data


# =============================================================================
# Schema Validation Tests
# =============================================================================


class TestSchemaValidation:
    """Tests for schema validation."""

    def test_research_query_defaults(self):
        """Test ResearchQuery default values."""
        query = ResearchQuery(query="test")

        assert query.max_results == 10
        assert query.include_clinical_trials is True
        assert query.include_guidelines is True
        assert query.date_range_years == 5

    def test_evidence_grade_enum(self):
        """Test EvidenceGrade enum."""
        assert EvidenceGrade.A.value == "A"
        assert EvidenceGrade.B.value == "B"
        assert EvidenceGrade.C.value == "C"

    def test_document_model(self):
        """Test Document model."""
        doc = Document(
            id="test-123",
            source_type=SourceType.PUBMED,
            title="Test Document",
            abstract="Test abstract",
            evidence_grade=EvidenceGrade.A,
        )

        assert doc.id == "test-123"
        assert doc.source_type == SourceType.PUBMED
        assert doc.relevance_score == 0.0  # Default

    def test_clinical_trial_model(self):
        """Test ClinicalTrial model."""
        trial = ClinicalTrial(
            nct_id="NCT12345678",
            title="Test Trial",
            status=TrialStatus.RECRUITING,
        )

        assert trial.nct_id == "NCT12345678"
        assert trial.status == TrialStatus.RECRUITING


# =============================================================================
# Integration Tests (with mocks)
# =============================================================================


class TestResearchAgentIntegration:
    """Integration tests with mocked external services."""

    @pytest.mark.asyncio
    async def test_full_search_pipeline(self):
        """Test complete search pipeline."""
        with patch.multiple(
            "app.agents.research",
            QueryExpander=MagicMock(),
            PubMedClient=MagicMock(),
            ClinicalTrialsClient=MagicMock(),
            get_embedding_service=MagicMock(),
            get_vector_store=MagicMock(),
        ):
            agent = ResearchAgent()

            # Mock query expansion
            agent.query_expander.expand_query = AsyncMock(
                return_value=ExpandedQuery(
                    original_query="test",
                    boolean_query="test OR testing",
                )
            )

            # Mock PubMed
            agent.pubmed_client.search_and_fetch = AsyncMock(return_value=MOCK_DOCUMENTS)

            # Mock trials
            agent.trials_client.search = AsyncMock(return_value=[])
            agent.trials_client.parse_trial = MagicMock()

            # Mock vector search
            agent._vector_search = AsyncMock(return_value=[])

            # Mock synthesis
            agent.synthesizer.synthesize = AsyncMock(
                return_value=MagicMock(
                    summary="Test summary",
                    key_findings=[],
                    contradictions=[],
                )
            )

            # Mock contradiction detection
            agent.contradiction_detector.detect = AsyncMock(return_value=[])

            # Execute search
            request = ResearchRequest(query=ResearchQuery(query="hypertension treatment"))

            response = await agent.search(request, use_cache=False)

            assert response.success is True
            assert response.result is not None
            assert len(response.result.documents) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
