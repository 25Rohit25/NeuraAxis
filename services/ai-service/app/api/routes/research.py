"""
NEURAXIS - Research API Endpoints
FastAPI routes for medical literature research
"""

import logging
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from app.agents.research import ResearchAgent, create_research_agent
from app.agents.research_schemas import (
    EvidenceGrade,
    IndexingJob,
    ResearchQuery,
    ResearchRequest,
    ResearchResponse,
    StudyType,
)
from app.core.security import get_current_user
from app.models.user import User
from app.services.pubmed import create_pubmed_client
from app.services.vector_store import get_vector_store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/research", tags=["research-ai"])


# =============================================================================
# Rate Limiting
# =============================================================================


class RateLimiter:
    """Simple in-memory rate limiter."""

    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = {}

    def check_limit(self, user_id: str) -> bool:
        """Check if user is within rate limit."""
        import time

        now = time.time()

        if user_id not in self._requests:
            self._requests[user_id] = []

        # Remove old requests
        self._requests[user_id] = [
            t for t in self._requests[user_id] if now - t < self.window_seconds
        ]

        if len(self._requests[user_id]) >= self.max_requests:
            return False

        self._requests[user_id].append(now)
        return True


# Global rate limiter
rate_limiter = RateLimiter(max_requests=20, window_seconds=60)


# =============================================================================
# Dependencies
# =============================================================================


async def get_research_agent() -> ResearchAgent:
    """Dependency to get research agent instance."""
    return create_research_agent()


async def check_rate_limit(
    current_user: User = Depends(get_current_user),
) -> User:
    """Check rate limit for user."""
    if not rate_limiter.check_limit(str(current_user.id)):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please try again later.",
        )
    return current_user


# =============================================================================
# API Endpoints
# =============================================================================


@router.post("", response_model=ResearchResponse)
async def search_medical_literature(
    request: ResearchRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(check_rate_limit),
    agent: ResearchAgent = Depends(get_research_agent),
    use_cache: bool = Query(True, description="Use cached results if available"),
):
    """
    Search medical literature and generate research synthesis.

    This endpoint:
    1. Expands query with medical synonyms
    2. Searches PubMed, ClinicalTrials.gov, and knowledge base
    3. Re-ranks results by relevance and recency
    4. Generates AI synthesis with citations
    5. Detects contradictions in findings

    **Response time target: <3 seconds** (excluding first-time queries)

    **Evidence Grades:**
    - **A**: Meta-analyses, systematic reviews, RCTs
    - **B**: Cohort studies, case-control studies
    - **C**: Case reports, expert opinion, other
    """
    logger.info(f"Research request from user {current_user.id}: {request.query.query[:50]}...")

    try:
        response = await agent.search(request, use_cache=use_cache)

        # Log research action in background
        if response.success and request.case_id:
            background_tasks.add_task(
                log_research_action,
                request.case_id,
                current_user.id,
                request.query.query,
                len(response.result.documents) if response.result else 0,
            )

        return response

    except Exception as e:
        logger.error(f"Research failed: {e}", exc_info=True)
        return ResearchResponse(
            success=False,
            error=f"Research failed: {str(e)}",
        )


@router.post("/quick")
async def quick_literature_search(
    query: str = Query(..., min_length=3, description="Search query"),
    max_results: int = Query(5, ge=1, le=20),
    current_user: User = Depends(check_rate_limit),
    agent: ResearchAgent = Depends(get_research_agent),
):
    """
    Quick literature search without full synthesis.

    Returns relevant documents without AI synthesis for faster response.
    """
    logger.info(f"Quick search from user {current_user.id}: {query[:50]}...")

    # Build simple request
    request = ResearchRequest(
        query=ResearchQuery(
            query=query,
            max_results=max_results,
            include_clinical_trials=False,
            include_guidelines=False,
        ),
    )

    # Get results
    response = await agent.search(request, use_cache=True)

    if response.success and response.result:
        # Return simplified response
        return {
            "success": True,
            "query": query,
            "documents": [
                {
                    "id": doc.id,
                    "title": doc.title,
                    "abstract": doc.abstract[:500] if doc.abstract else None,
                    "authors": [a.name for a in doc.authors[:3]],
                    "journal": doc.journal,
                    "year": doc.publication_date.year if doc.publication_date else None,
                    "evidence_grade": doc.evidence_grade.value if doc.evidence_grade else "C",
                    "pmid": doc.pmid,
                    "relevance_score": doc.combined_score,
                }
                for doc in response.result.documents
            ],
            "processing_time_ms": response.result.processing_time_ms,
        }
    else:
        return {
            "success": False,
            "error": response.error,
        }


@router.get("/pubmed/{pmid}")
async def get_pubmed_article(
    pmid: str,
    current_user: User = Depends(get_current_user),
):
    """
    Fetch a specific PubMed article by PMID.
    """
    pubmed = create_pubmed_client()

    try:
        articles = await pubmed.fetch_articles([pmid])

        if not articles:
            raise HTTPException(status_code=404, detail="Article not found")

        article = articles[0]

        return {
            "success": True,
            "article": {
                "pmid": article.pmid,
                "title": article.title,
                "abstract": article.abstract,
                "authors": [
                    {"name": a.name, "affiliation": a.affiliation} for a in article.authors
                ],
                "journal": article.journal,
                "publication_date": article.publication_date.isoformat()
                if article.publication_date
                else None,
                "doi": article.doi,
                "study_type": article.study_type.value if article.study_type else None,
                "evidence_grade": article.evidence_grade.value if article.evidence_grade else None,
                "mesh_terms": article.mesh_terms,
                "keywords": article.keywords,
            },
        }
    finally:
        await pubmed.close()


@router.get("/trials")
async def search_clinical_trials(
    query: str = Query(..., min_length=3),
    max_results: int = Query(10, ge=1, le=50),
    status: list[str] | None = Query(None, description="Filter by status"),
    current_user: User = Depends(get_current_user),
):
    """
    Search ClinicalTrials.gov for relevant trials.
    """
    from app.services.pubmed import create_clinical_trials_client

    client = create_clinical_trials_client()

    try:
        trials = await client.search(
            query=query,
            max_results=max_results,
            status=status,
        )

        parsed = [client.parse_trial(t) for t in trials]

        return {
            "success": True,
            "query": query,
            "total": len(parsed),
            "trials": parsed,
        }
    finally:
        await client.close()


@router.post("/expand-query")
async def expand_research_query(
    query: str = Query(..., min_length=3),
    current_user: User = Depends(get_current_user),
):
    """
    Expand a research query with medical synonyms and related terms.

    Useful for previewing how the query will be expanded before searching.
    """
    from app.agents.research import QueryExpander

    expander = QueryExpander()
    expanded = await expander.expand_query(query)

    return {
        "original_query": expanded.original_query,
        "medical_concepts": [
            {
                "term": c.term,
                "type": c.concept_type,
                "synonyms": c.synonyms,
                "mesh_id": c.mesh_id,
            }
            for c in expanded.medical_concepts
        ],
        "expanded_terms": expanded.expanded_terms,
        "boolean_query": expanded.boolean_query,
    }


@router.post("/index")
async def trigger_knowledge_base_indexing(
    source_type: str = Query(..., description="Source type to index"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: User = Depends(get_current_user),
):
    """
    Trigger background job to update knowledge base index.

    Requires admin privileges.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required",
        )

    from uuid import uuid4

    job_id = str(uuid4())

    # Add to background tasks
    background_tasks.add_task(
        run_indexing_job,
        job_id,
        source_type,
    )

    return {
        "success": True,
        "job_id": job_id,
        "status": "pending",
        "message": "Indexing job started in background",
    }


@router.get("/index/{job_id}")
async def get_indexing_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Get status of a knowledge base indexing job.
    """
    # In production, retrieve from database
    return {
        "job_id": job_id,
        "status": "unknown",
        "message": "Job tracking requires database integration",
    }


@router.get("/health")
async def research_health_check():
    """
    Health check for research service.
    """
    from app.core.config import settings

    checks = {
        "api_key_configured": bool(settings.OPENAI_API_KEY),
        "pubmed_available": True,
        "clinical_trials_available": True,
        "vector_store_type": "pinecone"
        if getattr(settings, "PINECONE_API_KEY", None)
        else "in_memory",
        "timestamp": datetime.now().isoformat(),
    }

    # Test PubMed connectivity
    try:
        pubmed = create_pubmed_client()
        pmids = await pubmed.search("test", max_results=1)
        checks["pubmed_available"] = len(pmids) > 0
        await pubmed.close()
    except Exception as e:
        checks["pubmed_available"] = False
        checks["pubmed_error"] = str(e)

    status_code = 200 if checks.get("api_key_configured") else 503

    return JSONResponse(status_code=status_code, content=checks)


# =============================================================================
# Background Tasks
# =============================================================================


async def log_research_action(
    case_id: str,
    user_id: str,
    query: str,
    results_count: int,
):
    """Log research action for audit."""
    logger.info(
        f"Research logged - Case: {case_id}, User: {user_id}, "
        f"Query: {query[:50]}, Results: {results_count}"
    )


async def run_indexing_job(job_id: str, source_type: str):
    """Run knowledge base indexing job."""
    logger.info(f"Starting indexing job {job_id} for {source_type}")

    try:
        # In production, this would:
        # 1. Fetch new documents from source
        # 2. Chunk documents
        # 3. Generate embeddings
        # 4. Upsert to vector store

        from app.services.vector_store import (
            DocumentChunker,
            get_embedding_service,
            get_vector_store,
        )

        # Placeholder implementation
        logger.info(f"Indexing job {job_id} completed")

    except Exception as e:
        logger.error(f"Indexing job {job_id} failed: {e}")
