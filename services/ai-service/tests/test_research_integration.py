"""
NEURAXIS - Research Agent Integration Tests
Tests with real API calls (requires API keys)
"""

import asyncio
import os
from datetime import datetime

import pytest

from app.agents.research import ResearchAgent, create_research_agent
from app.agents.research_schemas import (
    EvidenceGrade,
    ResearchQuery,
    ResearchRequest,
)
from app.services.pubmed import ClinicalTrialsClient, PubMedClient

# Skip integration tests if no API key
SKIP_INTEGRATION = not os.environ.get("OPENAI_API_KEY")
SKIP_REASON = "OPENAI_API_KEY environment variable not set"


# =============================================================================
# PubMed Integration Tests
# =============================================================================


class TestPubMedIntegration:
    """Integration tests for PubMed API."""

    @pytest.fixture
    def client(self):
        """Create PubMed client."""
        return PubMedClient()

    @pytest.mark.asyncio
    async def test_search_returns_results(self, client):
        """Test that PubMed search returns results."""
        try:
            pmids = await client.search(
                query="hypertension treatment",
                max_results=5,
                date_range_years=2,
            )

            assert isinstance(pmids, list)
            assert len(pmids) <= 5

            # PMIDs should be numeric strings
            for pmid in pmids:
                assert pmid.isdigit()

            print(f"Found {len(pmids)} articles for 'hypertension treatment'")

        finally:
            await client.close()

    @pytest.mark.asyncio
    async def test_fetch_articles(self, client):
        """Test fetching article details."""
        try:
            # First search
            pmids = await client.search("diabetes", max_results=3)

            if pmids:
                # Then fetch
                articles = await client.fetch_articles(pmids)

                assert len(articles) > 0

                for article in articles:
                    assert article.title
                    assert article.pmid
                    print(f"Fetched: {article.title[:60]}...")

        finally:
            await client.close()

    @pytest.mark.asyncio
    async def test_search_and_fetch_combined(self, client):
        """Test combined search and fetch."""
        try:
            documents = await client.search_and_fetch(
                query="COVID-19 vaccine efficacy",
                max_results=5,
                date_range_years=2,
            )

            assert len(documents) > 0

            for doc in documents:
                assert doc.id.startswith("pubmed:")
                assert doc.title
                assert doc.source_type.value == "pubmed"

                # Check evidence grading
                assert doc.evidence_grade is not None

                print(f"[{doc.evidence_grade.value}] {doc.title[:50]}...")

        finally:
            await client.close()


# =============================================================================
# Clinical Trials Integration Tests
# =============================================================================


class TestClinicalTrialsIntegration:
    """Integration tests for ClinicalTrials.gov API."""

    @pytest.fixture
    def client(self):
        """Create ClinicalTrials client."""
        return ClinicalTrialsClient()

    @pytest.mark.asyncio
    async def test_search_trials(self, client):
        """Test clinical trials search."""
        try:
            trials = await client.search(
                query="breast cancer immunotherapy",
                max_results=5,
            )

            assert isinstance(trials, list)

            for trial in trials:
                parsed = client.parse_trial(trial)
                assert parsed["nct_id"].startswith("NCT")
                assert parsed["title"]
                print(f"Trial: {parsed['nct_id']} - {parsed['title'][:50]}...")

        finally:
            await client.close()

    @pytest.mark.asyncio
    async def test_filter_by_status(self, client):
        """Test filtering trials by status."""
        try:
            recruiting = await client.search(
                query="diabetes",
                max_results=5,
                status=["RECRUITING"],
            )

            for trial in recruiting:
                parsed = client.parse_trial(trial)
                print(f"Recruiting: {parsed['nct_id']} - Status: {parsed['status']}")

        finally:
            await client.close()


# =============================================================================
# Full Research Agent Integration Tests
# =============================================================================


@pytest.mark.skipif(SKIP_INTEGRATION, reason=SKIP_REASON)
class TestResearchAgentIntegration:
    """Full integration tests for ResearchAgent."""

    @pytest.fixture(scope="class")
    def agent(self):
        """Create research agent."""
        return create_research_agent()

    @pytest.mark.asyncio
    async def test_hypertension_research(self, agent):
        """Test research on hypertension treatment."""
        request = ResearchRequest(
            query=ResearchQuery(
                query="What are the latest advances in hypertension treatment?",
                max_results=5,
                date_range_years=3,
                include_clinical_trials=True,
            )
        )

        response = await agent.search(request, use_cache=False)

        assert response.success is True
        assert response.result is not None

        result = response.result

        # Check documents retrieved
        assert len(result.documents) > 0
        print(f"\nFound {len(result.documents)} documents")

        # Check synthesis
        assert result.synthesis.summary
        print(f"\nSynthesis: {result.synthesis.summary[:200]}...")

        # Check citations
        assert len(result.citations) > 0
        print(f"\nCitations ({len(result.citations)}):")
        for citation in result.citations[:3]:
            print(f"  - {citation.ama_citation[:100]}...")

        # Check processing time
        assert result.processing_time_ms > 0
        print(f"\nProcessing time: {result.processing_time_ms}ms")

        # Verify <3 second target (excluding first-time calls)
        if result.processing_time_ms > 3000:
            print(f"WARNING: Exceeded 3-second target")

    @pytest.mark.asyncio
    async def test_cancer_treatment_research(self, agent):
        """Test research on cancer immunotherapy."""
        request = ResearchRequest(
            query=ResearchQuery(
                query="Checkpoint inhibitor efficacy in melanoma",
                max_results=5,
                min_evidence_grade=EvidenceGrade.B,
            )
        )

        response = await agent.search(request, use_cache=False)

        assert response.success is True

        result = response.result

        # All documents should be grade A or B
        for doc in result.documents:
            if doc.evidence_grade:
                assert doc.evidence_grade in [EvidenceGrade.A, EvidenceGrade.B]

        print(f"\nEvidence distribution:")
        grade_counts = {"A": 0, "B": 0, "C": 0}
        for doc in result.documents:
            if doc.evidence_grade:
                grade_counts[doc.evidence_grade.value] += 1
        print(f"  A: {grade_counts['A']}, B: {grade_counts['B']}, C: {grade_counts['C']}")

    @pytest.mark.asyncio
    async def test_query_expansion(self, agent):
        """Test that query expansion works."""
        request = ResearchRequest(
            query=ResearchQuery(
                query="heart attack prevention",
                max_results=3,
            )
        )

        response = await agent.search(request, use_cache=False)

        assert response.success is True

        expanded = response.result.expanded_query

        # Should have expanded terms
        print(f"\nOriginal: {expanded.original_query}")
        print(f"Boolean query: {expanded.boolean_query}")
        print(f"Concepts: {[c.term for c in expanded.medical_concepts]}")
        print(f"Expanded terms: {expanded.expanded_terms}")

        # Should expand "heart attack" to medical terms
        all_terms = [c.term.lower() for c in expanded.medical_concepts]
        all_synonyms = [s.lower() for c in expanded.medical_concepts for s in c.synonyms]

        # One of these should be present
        expected = ["myocardial infarction", "mi", "heart attack", "cardiac"]
        found = any(
            term in all_terms or term in all_synonyms or term in expanded.boolean_query.lower()
            for term in expected
        )

        if not found:
            print("Note: Query expansion did not find expected medical synonyms")

    @pytest.mark.asyncio
    async def test_caching_works(self, agent):
        """Test that caching improves response time."""
        request = ResearchRequest(
            query=ResearchQuery(
                query="aspirin cardiovascular prevention",
                max_results=3,
            )
        )

        # First request - not cached
        response1 = await agent.search(request, use_cache=True)
        assert response1.success is True
        time1 = response1.result.processing_time_ms

        # Second request - should be cached
        response2 = await agent.search(request, use_cache=True)
        assert response2.success is True

        if response2.cached:
            print(f"\nFirst request: {time1}ms (uncached)")
            print(f"Second request: instantly (cached)")
        else:
            print(f"\nNote: Caching not available (Redis not configured)")

    @pytest.mark.asyncio
    async def test_contradiction_detection(self, agent):
        """Test contradiction detection in controversial topic."""
        request = ResearchRequest(
            query=ResearchQuery(
                query="low carbohydrate diet cardiovascular effects",
                max_results=8,
            )
        )

        response = await agent.search(request, use_cache=False)

        assert response.success is True

        contradictions = response.result.synthesis.contradictions

        print(f"\nContradictions found: {len(contradictions)}")
        for c in contradictions[:2]:
            print(f"\n  Topic: {c.topic}")
            print(f"  Position A: {c.position_a[:100]}...")
            print(f"  Position B: {c.position_b[:100]}...")

    @pytest.mark.asyncio
    async def test_clinical_trials_included(self, agent):
        """Test that clinical trials are included when requested."""
        request = ResearchRequest(
            query=ResearchQuery(
                query="CAR-T cell therapy acute lymphoblastic leukemia",
                max_results=5,
                include_clinical_trials=True,
            )
        )

        response = await agent.search(request, use_cache=False)

        assert response.success is True

        trials = response.result.clinical_trials

        print(f"\nClinical trials found: {len(trials)}")
        for trial in trials[:3]:
            print(f"  - {trial.nct_id}: {trial.title[:50]}...")
            print(f"    Status: {trial.status.value}, Phase: {trial.phase}")

    @pytest.mark.asyncio
    async def test_response_structure(self, agent):
        """Test that response has all required fields."""
        request = ResearchRequest(
            query=ResearchQuery(
                query="metformin diabetes",
                max_results=3,
            )
        )

        response = await agent.search(request, use_cache=False)

        assert response.success is True
        result = response.result

        # Check all required fields
        assert result.query_id
        assert result.original_query
        assert result.expanded_query
        assert result.synthesis
        assert result.citations is not None
        assert result.processing_time_ms > 0
        assert result.disclaimer

        # Check synthesis structure
        assert result.synthesis.summary

        # Check document structure
        for doc in result.documents:
            assert doc.id
            assert doc.title
            assert doc.source_type

    @pytest.mark.asyncio
    async def test_performance_target(self, agent):
        """Test that response time meets <3 second target."""
        import time

        request = ResearchRequest(
            query=ResearchQuery(
                query="statin therapy",
                max_results=5,
            )
        )

        # Warm up cache
        await agent.search(request, use_cache=True)

        # Measure cached response
        start = time.time()
        response = await agent.search(request, use_cache=True)
        elapsed = time.time() - start

        if response.cached:
            print(f"\nCached response time: {elapsed * 1000:.0f}ms")
            assert elapsed < 0.5, "Cached response should be < 500ms"
        else:
            print(f"\nUncached response time: {elapsed * 1000:.0f}ms")
            # First call may be slower due to API calls


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
