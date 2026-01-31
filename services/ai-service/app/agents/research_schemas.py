"""
NEURAXIS - Research Agent Schemas
Pydantic models for medical literature research
"""

from datetime import datetime
from enum import Enum
from typing import Annotated

from pydantic import BaseModel, Field

# =============================================================================
# Enums
# =============================================================================


class EvidenceGrade(str, Enum):
    """Evidence quality grading."""

    A = "A"  # High quality - RCTs, meta-analyses, systematic reviews
    B = "B"  # Moderate quality - cohort studies, case-control
    C = "C"  # Low quality - case reports, expert opinion, guidelines


class SourceType(str, Enum):
    """Type of research source."""

    PUBMED = "pubmed"
    CLINICAL_TRIAL = "clinical_trial"
    GUIDELINE = "guideline"
    KNOWLEDGE_BASE = "knowledge_base"


class StudyType(str, Enum):
    """Type of clinical study."""

    META_ANALYSIS = "meta_analysis"
    SYSTEMATIC_REVIEW = "systematic_review"
    RCT = "randomized_controlled_trial"
    COHORT = "cohort_study"
    CASE_CONTROL = "case_control"
    CASE_REPORT = "case_report"
    REVIEW = "review"
    GUIDELINE = "clinical_guideline"
    EXPERT_OPINION = "expert_opinion"
    OTHER = "other"


class TrialStatus(str, Enum):
    """Clinical trial status."""

    RECRUITING = "recruiting"
    ACTIVE = "active"
    COMPLETED = "completed"
    TERMINATED = "terminated"
    SUSPENDED = "suspended"
    WITHDRAWN = "withdrawn"
    UNKNOWN = "unknown"


# =============================================================================
# Document Models
# =============================================================================


class Author(BaseModel):
    """Research paper author."""

    name: str
    affiliation: str | None = None


class Citation(BaseModel):
    """Formatted citation for a source."""

    source_id: str
    source_type: SourceType
    ama_citation: str = Field(description="AMA style citation")
    authors: list[Author] = Field(default_factory=list)
    title: str
    journal: str | None = None
    year: int | None = None
    volume: str | None = None
    issue: str | None = None
    pages: str | None = None
    doi: str | None = None
    pmid: str | None = None
    url: str | None = None


class Document(BaseModel):
    """Retrieved document from knowledge base."""

    id: str
    source_type: SourceType
    title: str
    abstract: str | None = None
    content: str | None = None
    authors: list[Author] = Field(default_factory=list)
    publication_date: datetime | None = None
    journal: str | None = None
    doi: str | None = None
    pmid: str | None = None
    study_type: StudyType | None = None
    evidence_grade: EvidenceGrade | None = None
    keywords: list[str] = Field(default_factory=list)
    mesh_terms: list[str] = Field(default_factory=list)

    # Retrieval metadata
    relevance_score: float = 0.0
    recency_score: float = 0.0
    combined_score: float = 0.0
    snippet: str | None = None


class ClinicalTrial(BaseModel):
    """Clinical trial information."""

    nct_id: str
    title: str
    status: TrialStatus
    phase: str | None = None
    conditions: list[str] = Field(default_factory=list)
    interventions: list[str] = Field(default_factory=list)
    sponsor: str | None = None
    start_date: datetime | None = None
    completion_date: datetime | None = None
    enrollment: int | None = None
    location: str | None = None
    summary: str | None = None
    url: str | None = None
    relevance_score: float = 0.0


# =============================================================================
# Query Models
# =============================================================================


class MedicalConcept(BaseModel):
    """Extracted medical concept from query."""

    term: str
    concept_type: str = Field(description="disease, drug, procedure, symptom, etc.")
    synonyms: list[str] = Field(default_factory=list)
    mesh_id: str | None = None
    umls_cui: str | None = None


class ExpandedQuery(BaseModel):
    """Query with expanded terms."""

    original_query: str
    medical_concepts: list[MedicalConcept] = Field(default_factory=list)
    expanded_terms: list[str] = Field(default_factory=list)
    boolean_query: str | None = None
    filters: dict = Field(default_factory=dict)


class ResearchQuery(BaseModel):
    """Research query input."""

    query: str = Field(description="Natural language research query")
    max_results: int = Field(default=10, ge=1, le=50)
    include_clinical_trials: bool = True
    include_guidelines: bool = True
    date_range_years: int | None = Field(default=5, description="Limit to recent years")
    study_types: list[StudyType] | None = None
    min_evidence_grade: EvidenceGrade | None = None


# =============================================================================
# Synthesis Models
# =============================================================================


class KeyFinding(BaseModel):
    """Key finding from research synthesis."""

    finding: str
    source_ids: list[str] = Field(description="IDs of supporting sources")
    evidence_grade: EvidenceGrade
    confidence: float = Field(ge=0, le=1)


class Contradiction(BaseModel):
    """Detected contradiction in literature."""

    topic: str
    position_a: str
    sources_a: list[str]
    position_b: str
    sources_b: list[str]
    resolution: str | None = None


class ResearchSynthesis(BaseModel):
    """Synthesized research findings."""

    summary: str = Field(description="Comprehensive summary of findings")
    key_findings: list[KeyFinding] = Field(default_factory=list)
    clinical_implications: list[str] = Field(default_factory=list)
    knowledge_gaps: list[str] = Field(default_factory=list)
    contradictions: list[Contradiction] = Field(default_factory=list)
    methodology_notes: str | None = None


# =============================================================================
# Response Models
# =============================================================================


class ResearchResult(BaseModel):
    """Complete research result."""

    query_id: str
    original_query: str
    expanded_query: ExpandedQuery

    # Retrieved documents
    documents: list[Document] = Field(default_factory=list)
    clinical_trials: list[ClinicalTrial] = Field(default_factory=list)

    # Synthesis
    synthesis: ResearchSynthesis
    citations: list[Citation] = Field(default_factory=list)

    # Metadata
    total_sources_searched: int = 0
    total_documents_retrieved: int = 0
    processing_time_ms: int = 0
    tokens_used: int | None = None
    cached: bool = False

    # Quality
    overall_evidence_grade: EvidenceGrade | None = None
    confidence_score: float = Field(ge=0, le=1, default=0.5)

    # Disclaimer
    disclaimer: str = Field(
        default=(
            "This research summary is generated by AI and should be verified "
            "against primary sources. It is for informational purposes only "
            "and does not constitute medical advice."
        )
    )


class ResearchRequest(BaseModel):
    """API request for research."""

    query: ResearchQuery
    case_id: str | None = None
    user_context: str | None = Field(
        default=None, description="Additional context about the research need"
    )


class ResearchResponse(BaseModel):
    """API response wrapper."""

    success: bool
    result: ResearchResult | None = None
    error: str | None = None
    cached: bool = False


# =============================================================================
# Vector Store Models
# =============================================================================


class DocumentChunk(BaseModel):
    """Chunk of document for vector storage."""

    id: str
    document_id: str
    chunk_index: int
    content: str
    embedding: list[float] | None = None
    metadata: dict = Field(default_factory=dict)


class VectorSearchResult(BaseModel):
    """Result from vector search."""

    id: str
    score: float
    metadata: dict = Field(default_factory=dict)
    content: str | None = None


class IndexingJob(BaseModel):
    """Background job for knowledge base indexing."""

    job_id: str
    status: str  # pending, running, completed, failed
    source_type: SourceType
    documents_processed: int = 0
    documents_total: int = 0
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error: str | None = None
