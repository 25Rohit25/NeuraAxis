"""
NEURAXIS - Research Agent
RAG-based medical literature research with synthesis
"""

import asyncio
import hashlib
import json
import logging
import time
from datetime import datetime
from typing import Any
from uuid import uuid4

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from app.agents.research_schemas import (
    Author,
    Citation,
    ClinicalTrial,
    Contradiction,
    Document,
    EvidenceGrade,
    ExpandedQuery,
    KeyFinding,
    MedicalConcept,
    ResearchQuery,
    ResearchRequest,
    ResearchResponse,
    ResearchResult,
    ResearchSynthesis,
    SourceType,
    TrialStatus,
    VectorSearchResult,
)
from app.core.config import settings
from app.core.redis import get_redis_client
from app.services.pubmed import ClinicalTrialsClient, PubMedClient
from app.services.vector_store import (
    EmbeddingService,
    get_embedding_service,
    get_vector_store,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Query Expansion
# =============================================================================

QUERY_EXPANSION_PROMPT = """You are a medical terminology expert. Analyze the following research query and extract key medical concepts, synonyms, and related terms to improve literature search.

Query: {query}

Respond with a JSON object containing:
{{
    "medical_concepts": [
        {{
            "term": "main medical term",
            "concept_type": "disease|drug|procedure|symptom|gene|protein|other",
            "synonyms": ["synonym1", "synonym2"],
            "mesh_id": "optional MeSH ID if known"
        }}
    ],
    "expanded_terms": ["additional related terms for search"],
    "boolean_query": "PubMed-style boolean query combining concepts"
}}

Focus on:
1. Medical synonyms (e.g., "heart attack" = "myocardial infarction" = "MI")
2. Drug generic/brand names
3. Related conditions or procedures
4. MeSH terms when applicable

Respond with valid JSON only."""


class QueryExpander:
    """Expand medical queries with synonyms and related terms."""

    def __init__(self, llm: ChatOpenAI | None = None):
        self.llm = llm or ChatOpenAI(
            model="gpt-4o",
            temperature=0,
            api_key=settings.OPENAI_API_KEY,
        )

        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "You are a medical terminology expert."),
                ("human", QUERY_EXPANSION_PROMPT),
            ]
        )

    async def expand_query(self, query: str) -> ExpandedQuery:
        """
        Expand query with medical synonyms and related terms.

        Args:
            query: Original search query

        Returns:
            ExpandedQuery with concepts and expanded terms
        """
        try:
            chain = self.prompt | self.llm
            response = await chain.ainvoke({"query": query})

            # Parse JSON response
            content = response.content
            if isinstance(content, str):
                data = json.loads(content)
            else:
                data = content

            concepts = []
            for c in data.get("medical_concepts", []):
                concepts.append(
                    MedicalConcept(
                        term=c.get("term", ""),
                        concept_type=c.get("concept_type", "other"),
                        synonyms=c.get("synonyms", []),
                        mesh_id=c.get("mesh_id"),
                    )
                )

            return ExpandedQuery(
                original_query=query,
                medical_concepts=concepts,
                expanded_terms=data.get("expanded_terms", []),
                boolean_query=data.get("boolean_query"),
            )

        except Exception as e:
            logger.warning(f"Query expansion failed: {e}")
            return ExpandedQuery(
                original_query=query,
                medical_concepts=[],
                expanded_terms=[],
            )


# =============================================================================
# Re-ranking with RRF
# =============================================================================


class ReRanker:
    """
    Re-rank documents using Reciprocal Rank Fusion (RRF).
    Combines relevance and recency scores.
    """

    RRF_K = 60  # Constant for RRF formula
    RECENCY_WEIGHT = 0.3  # Weight for recency in combined score

    def rerank(
        self,
        documents: list[Document],
        query: str,
    ) -> list[Document]:
        """
        Re-rank documents by combined relevance and recency.

        Args:
            documents: Documents to rerank
            query: Original query (for context)

        Returns:
            Reranked list of documents
        """
        if not documents:
            return []

        # Calculate recency scores
        now = datetime.now()
        for doc in documents:
            if doc.publication_date:
                days_old = (now - doc.publication_date).days
                # Exponential decay: halves every 365 days
                doc.recency_score = 0.5 ** (days_old / 365)
            else:
                doc.recency_score = 0.1  # Low score for unknown dates

        # Sort by relevance and get ranks
        docs_by_relevance = sorted(documents, key=lambda d: d.relevance_score, reverse=True)
        relevance_ranks = {d.id: i + 1 for i, d in enumerate(docs_by_relevance)}

        # Sort by recency and get ranks
        docs_by_recency = sorted(documents, key=lambda d: d.recency_score, reverse=True)
        recency_ranks = {d.id: i + 1 for i, d in enumerate(docs_by_recency)}

        # Calculate RRF combined scores
        for doc in documents:
            relevance_rrf = 1 / (self.RRF_K + relevance_ranks[doc.id])
            recency_rrf = 1 / (self.RRF_K + recency_ranks[doc.id])

            # Combined score with weighting
            doc.combined_score = (
                1 - self.RECENCY_WEIGHT
            ) * relevance_rrf + self.RECENCY_WEIGHT * recency_rrf

        # Sort by combined score
        documents.sort(key=lambda d: d.combined_score, reverse=True)

        return documents

    def deduplicate(
        self,
        documents: list[Document],
        similarity_threshold: float = 0.9,
    ) -> list[Document]:
        """
        Remove duplicate documents based on title similarity.

        Args:
            documents: Documents to deduplicate
            similarity_threshold: Jaccard similarity threshold

        Returns:
            Deduplicated list
        """
        if not documents:
            return []

        unique_docs = []
        seen_titles: list[set] = []

        for doc in documents:
            title_words = set(doc.title.lower().split())

            is_duplicate = False
            for seen in seen_titles:
                # Jaccard similarity
                intersection = len(title_words & seen)
                union = len(title_words | seen)
                if union > 0 and intersection / union >= similarity_threshold:
                    is_duplicate = True
                    break

            if not is_duplicate:
                unique_docs.append(doc)
                seen_titles.append(title_words)

        return unique_docs


# =============================================================================
# Citation Formatter
# =============================================================================


class CitationFormatter:
    """Format citations in AMA (American Medical Association) style."""

    def format_ama(self, document: Document) -> str:
        """
        Format document as AMA citation.

        Format: Author(s). Title. Journal. Year;Volume(Issue):Pages. doi:DOI

        Args:
            document: Document to cite

        Returns:
            AMA formatted citation string
        """
        parts = []

        # Authors
        if document.authors:
            author_names = []
            for i, author in enumerate(document.authors[:6]):
                author_names.append(author.name)

            if len(document.authors) > 6:
                author_names.append("et al")

            parts.append(", ".join(author_names) + ".")

        # Title
        title = document.title.rstrip(".")
        parts.append(f"{title}.")

        # Journal
        if document.journal:
            parts.append(f"{document.journal}.")

        # Year and volume info
        year_info = []
        if document.publication_date:
            year_info.append(str(document.publication_date.year))
        if year_info:
            parts.append(f"{''.join(year_info)}")

        # DOI or PMID
        if document.doi:
            parts.append(f"doi:{document.doi}")
        elif document.pmid:
            parts.append(f"PMID: {document.pmid}")

        return " ".join(parts)

    def create_citation(self, document: Document) -> Citation:
        """Create Citation object from Document."""
        return Citation(
            source_id=document.id,
            source_type=document.source_type,
            ama_citation=self.format_ama(document),
            authors=document.authors,
            title=document.title,
            journal=document.journal,
            year=document.publication_date.year if document.publication_date else None,
            doi=document.doi,
            pmid=document.pmid,
            url=f"https://pubmed.ncbi.nlm.nih.gov/{document.pmid}/" if document.pmid else None,
        )


# =============================================================================
# Contradiction Detector
# =============================================================================

CONTRADICTION_PROMPT = """Analyze the following research paper excerpts and identify any contradictions or conflicting findings on the topic.

Topic: {topic}

Sources:
{sources}

Identify contradictions where different studies reach opposite conclusions. For each contradiction found, explain:
1. What the disagreement is about
2. Which sources support each position
3. Possible resolution or explanation

Respond with JSON:
{{
    "contradictions": [
        {{
            "topic": "specific topic of disagreement",
            "position_a": "first position",
            "sources_a": ["source_id1"],
            "position_b": "opposing position",
            "sources_b": ["source_id2"],
            "resolution": "possible explanation for difference, if any"
        }}
    ]
}}

If no contradictions are found, return empty array. Respond with JSON only."""


class ContradictionDetector:
    """Detect contradictions in research findings."""

    def __init__(self, llm: ChatOpenAI | None = None):
        self.llm = llm or ChatOpenAI(
            model="gpt-4o",
            temperature=0,
            api_key=settings.OPENAI_API_KEY,
        )

        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "You are a scientific literature analyst."),
                ("human", CONTRADICTION_PROMPT),
            ]
        )

    async def detect(
        self,
        topic: str,
        documents: list[Document],
    ) -> list[Contradiction]:
        """
        Detect contradictions in document set.

        Args:
            topic: Research topic
            documents: Documents to analyze

        Returns:
            List of detected contradictions
        """
        if len(documents) < 2:
            return []

        # Format sources for prompt
        sources_text = ""
        for doc in documents[:10]:  # Limit to avoid token overflow
            snippet = (doc.abstract or doc.content or "")[:500]
            sources_text += f"\n[{doc.id}] {doc.title}\n{snippet}\n"

        try:
            chain = self.prompt | self.llm
            response = await chain.ainvoke(
                {
                    "topic": topic,
                    "sources": sources_text,
                }
            )

            # Parse response
            content = response.content
            if isinstance(content, str):
                data = json.loads(content)
            else:
                data = content

            contradictions = []
            for c in data.get("contradictions", []):
                contradictions.append(
                    Contradiction(
                        topic=c.get("topic", ""),
                        position_a=c.get("position_a", ""),
                        sources_a=c.get("sources_a", []),
                        position_b=c.get("position_b", ""),
                        sources_b=c.get("sources_b", []),
                        resolution=c.get("resolution"),
                    )
                )

            return contradictions

        except Exception as e:
            logger.warning(f"Contradiction detection failed: {e}")
            return []


# =============================================================================
# Research Synthesis
# =============================================================================

SYNTHESIS_PROMPT = """You are a medical research synthesizer. Analyze the following research sources and create a comprehensive summary on the topic.

Research Question: {query}

Sources (numbered for citation):
{sources}

Create a synthesis that:
1. Summarizes key findings across all sources
2. Identifies areas of consensus and disagreement
3. Notes the strength of evidence (based on study types)
4. Highlights clinical implications
5. Identifies gaps in current knowledge

Use citations in the format [1], [2], etc. to reference specific sources.

Respond with JSON:
{{
    "summary": "Comprehensive synthesis paragraph with citations",
    "key_findings": [
        {{
            "finding": "Key finding statement",
            "source_ids": ["source_id1", "source_id2"],
            "evidence_grade": "A|B|C",
            "confidence": 0.0-1.0
        }}
    ],
    "clinical_implications": ["Implication 1", "Implication 2"],
    "knowledge_gaps": ["Gap 1", "Gap 2"],
    "methodology_notes": "Notes about study methodologies"
}}

Be thorough but concise. Respond with JSON only."""


class ResearchSynthesizer:
    """Synthesize research findings from multiple sources."""

    MAX_CONTEXT_TOKENS = 4000  # Max tokens for context

    def __init__(self, llm: ChatOpenAI | None = None):
        self.llm = llm or ChatOpenAI(
            model="gpt-4o",
            temperature=0.1,
            api_key=settings.OPENAI_API_KEY,
            model_kwargs={"response_format": {"type": "json_object"}},
        )

        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "You are a medical research synthesizer."),
                ("human", SYNTHESIS_PROMPT),
            ]
        )

    def _assemble_context(
        self,
        documents: list[Document],
        max_chars: int = 12000,  # ~3000 tokens
    ) -> tuple[str, dict[str, str]]:
        """
        Assemble context from documents within token limit.

        Returns:
            Tuple of (formatted sources text, id to citation number mapping)
        """
        sources_text = ""
        id_to_num: dict[str, str] = {}
        current_chars = 0

        for i, doc in enumerate(documents, 1):
            # Get content
            content = doc.abstract or doc.content or ""
            title = doc.title

            # Estimate addition size
            grade = doc.evidence_grade.value if doc.evidence_grade else "C"
            entry = f"\n[{i}] {title} (Evidence: {grade})\n{content}\n"

            if current_chars + len(entry) > max_chars:
                # Truncate this entry
                remaining = max_chars - current_chars - 100
                if remaining > 200:
                    entry = f"\n[{i}] {title} (Evidence: {grade})\n{content[:remaining]}...\n"
                else:
                    break

            sources_text += entry
            id_to_num[doc.id] = str(i)
            current_chars += len(entry)

        return sources_text, id_to_num

    async def synthesize(
        self,
        query: str,
        documents: list[Document],
    ) -> ResearchSynthesis:
        """
        Generate synthesis from documents.

        Args:
            query: Research query
            documents: Source documents

        Returns:
            ResearchSynthesis object
        """
        if not documents:
            return ResearchSynthesis(
                summary="No relevant research sources found for this query.",
                key_findings=[],
                clinical_implications=[],
                knowledge_gaps=["Further research needed on this topic."],
            )

        # Assemble context
        sources_text, id_map = self._assemble_context(documents)

        try:
            chain = self.prompt | self.llm
            response = await chain.ainvoke(
                {
                    "query": query,
                    "sources": sources_text,
                }
            )

            # Parse response
            content = response.content
            if isinstance(content, str):
                data = json.loads(content)
            else:
                data = content

            # Convert citation numbers back to IDs
            key_findings = []
            for kf in data.get("key_findings", []):
                # Map source numbers to IDs
                source_ids = []
                for sid in kf.get("source_ids", []):
                    # Find matching document ID
                    for doc_id, num in id_map.items():
                        if num == str(sid) or doc_id == sid:
                            source_ids.append(doc_id)
                            break

                key_findings.append(
                    KeyFinding(
                        finding=kf.get("finding", ""),
                        source_ids=source_ids or kf.get("source_ids", []),
                        evidence_grade=EvidenceGrade(kf.get("evidence_grade", "C")),
                        confidence=float(kf.get("confidence", 0.5)),
                    )
                )

            return ResearchSynthesis(
                summary=data.get("summary", ""),
                key_findings=key_findings,
                clinical_implications=data.get("clinical_implications", []),
                knowledge_gaps=data.get("knowledge_gaps", []),
                methodology_notes=data.get("methodology_notes"),
            )

        except Exception as e:
            logger.error(f"Synthesis failed: {e}")
            return ResearchSynthesis(
                summary=f"Error generating synthesis: {str(e)}",
                key_findings=[],
            )


# =============================================================================
# Main Research Agent
# =============================================================================


class ResearchAgent:
    """
    RAG-based research agent for medical literature search.

    Pipeline:
    1. Query understanding and expansion
    2. Multi-source search (PubMed, clinical trials, knowledge base)
    3. Vector search for semantic matching
    4. Re-ranking with RRF
    5. Context assembly with deduplication
    6. GPT-4o synthesis with citations
    7. Contradiction detection
    """

    CACHE_TTL = 3600  # 1 hour

    def __init__(self):
        # Initialize components
        self.query_expander = QueryExpander()
        self.pubmed_client = PubMedClient()
        self.trials_client = ClinicalTrialsClient()
        self.embedding_service = get_embedding_service()
        self.vector_store = get_vector_store()
        self.reranker = ReRanker()
        self.citation_formatter = CitationFormatter()
        self.contradiction_detector = ContradictionDetector()
        self.synthesizer = ResearchSynthesizer()

        self.redis_client = None

        logger.info("ResearchAgent initialized")

    async def _get_redis(self):
        """Get Redis client for caching."""
        if self.redis_client is None:
            self.redis_client = await get_redis_client()
        return self.redis_client

    def _generate_cache_key(self, query: ResearchQuery) -> str:
        """Generate cache key for query."""
        data = {
            "query": query.query,
            "max_results": query.max_results,
            "date_range": query.date_range_years,
            "include_trials": query.include_clinical_trials,
        }
        data_str = json.dumps(data, sort_keys=True)
        return f"research:{hashlib.sha256(data_str.encode()).hexdigest()[:32]}"

    async def _get_cached(self, cache_key: str) -> ResearchResult | None:
        """Get cached result."""
        try:
            redis = await self._get_redis()
            if redis:
                cached = await redis.get(cache_key)
                if cached:
                    logger.info(f"Cache hit for research query")
                    return ResearchResult(**json.loads(cached))
        except Exception as e:
            logger.warning(f"Cache retrieval failed: {e}")
        return None

    async def _cache_result(self, cache_key: str, result: ResearchResult):
        """Cache result."""
        try:
            redis = await self._get_redis()
            if redis:
                await redis.setex(
                    cache_key,
                    self.CACHE_TTL,
                    result.model_dump_json(),
                )
        except Exception as e:
            logger.warning(f"Cache storage failed: {e}")

    async def search(
        self,
        request: ResearchRequest,
        use_cache: bool = True,
    ) -> ResearchResponse:
        """
        Execute research pipeline.

        Args:
            request: Research request
            use_cache: Whether to use cached results

        Returns:
            ResearchResponse with results or error
        """
        query_id = str(uuid4())
        start_time = time.time()

        logger.info(f"Starting research - Query ID: {query_id}")

        try:
            query = request.query

            # Check cache
            cache_key = self._generate_cache_key(query)
            if use_cache:
                cached = await self._get_cached(cache_key)
                if cached:
                    return ResearchResponse(
                        success=True,
                        result=cached,
                        cached=True,
                    )

            # 1. Query expansion
            expanded_query = await self.query_expander.expand_query(query.query)

            # 2. Multi-source search (parallel)
            search_query = expanded_query.boolean_query or query.query

            search_tasks = [
                self.pubmed_client.search_and_fetch(
                    query=search_query,
                    max_results=query.max_results * 2,  # Fetch more for reranking
                    date_range_years=query.date_range_years,
                ),
            ]

            if query.include_clinical_trials:
                search_tasks.append(self._search_clinical_trials(query.query, query.max_results))

            results = await asyncio.gather(*search_tasks, return_exceptions=True)

            # Process results
            documents: list[Document] = []
            clinical_trials: list[ClinicalTrial] = []

            if len(results) > 0 and not isinstance(results[0], Exception):
                documents.extend(results[0])

            if len(results) > 1 and not isinstance(results[1], Exception):
                clinical_trials.extend(results[1])

            # 3. Vector search in knowledge base
            if documents:
                vector_results = await self._vector_search(
                    query.query,
                    top_k=query.max_results,
                )

                # Merge relevance scores
                for doc in documents:
                    for vr in vector_results:
                        if vr.id == doc.id or doc.id.endswith(vr.id):
                            doc.relevance_score = vr.score
                            break

                    if doc.relevance_score == 0:
                        doc.relevance_score = 0.5  # Default score

            # 4. Rerank and deduplicate
            documents = self.reranker.deduplicate(documents)
            documents = self.reranker.rerank(documents, query.query)

            # Limit to requested results
            documents = documents[: query.max_results]

            # 5. Filter by evidence grade if specified
            if query.min_evidence_grade:
                grade_order = {"A": 0, "B": 1, "C": 2}
                min_order = grade_order.get(query.min_evidence_grade.value, 2)
                documents = [
                    d
                    for d in documents
                    if grade_order.get(d.evidence_grade.value if d.evidence_grade else "C", 2)
                    <= min_order
                ]

            # 6. Generate synthesis
            synthesis = await self.synthesizer.synthesize(query.query, documents)

            # 7. Detect contradictions
            contradictions = await self.contradiction_detector.detect(
                query.query,
                documents,
            )
            synthesis.contradictions = contradictions

            # 8. Format citations
            citations = [self.citation_formatter.create_citation(doc) for doc in documents]

            # Calculate overall evidence grade
            overall_grade = self._calculate_overall_grade(documents)

            # Build result
            processing_time_ms = int((time.time() - start_time) * 1000)

            result = ResearchResult(
                query_id=query_id,
                original_query=query.query,
                expanded_query=expanded_query,
                documents=documents,
                clinical_trials=clinical_trials,
                synthesis=synthesis,
                citations=citations,
                total_sources_searched=3,  # PubMed, trials, knowledge base
                total_documents_retrieved=len(documents) + len(clinical_trials),
                processing_time_ms=processing_time_ms,
                cached=False,
                overall_evidence_grade=overall_grade,
                confidence_score=self._calculate_confidence(documents, synthesis),
            )

            # Cache result
            if use_cache:
                await self._cache_result(cache_key, result)

            logger.info(
                f"Research complete - Query ID: {query_id}, "
                f"Documents: {len(documents)}, Time: {processing_time_ms}ms"
            )

            return ResearchResponse(
                success=True,
                result=result,
                cached=False,
            )

        except Exception as e:
            logger.error(f"Research failed: {e}", exc_info=True)
            return ResearchResponse(
                success=False,
                error=str(e),
            )

    async def _search_clinical_trials(
        self,
        query: str,
        max_results: int,
    ) -> list[ClinicalTrial]:
        """Search clinical trials."""
        try:
            trials = await self.trials_client.search(
                query=query,
                max_results=max_results,
            )

            parsed_trials = []
            for trial_data in trials:
                parsed = self.trials_client.parse_trial(trial_data)

                parsed_trials.append(
                    ClinicalTrial(
                        nct_id=parsed["nct_id"],
                        title=parsed["title"],
                        status=TrialStatus(parsed["status"]),
                        phase=parsed["phase"],
                        conditions=parsed["conditions"],
                        interventions=parsed["interventions"],
                        sponsor=parsed["sponsor"],
                        start_date=parsed["start_date"],
                        completion_date=parsed["completion_date"],
                        enrollment=parsed["enrollment"],
                        summary=parsed["summary"],
                        url=parsed["url"],
                    )
                )

            return parsed_trials

        except Exception as e:
            logger.warning(f"Clinical trials search failed: {e}")
            return []

    async def _vector_search(
        self,
        query: str,
        top_k: int = 10,
    ) -> list[VectorSearchResult]:
        """Search vector store."""
        try:
            query_embedding = self.embedding_service.embed_text(query)
            results = await self.vector_store.search(
                query_embedding=query_embedding,
                top_k=top_k,
            )
            return results
        except Exception as e:
            logger.warning(f"Vector search failed: {e}")
            return []

    def _calculate_overall_grade(
        self,
        documents: list[Document],
    ) -> EvidenceGrade | None:
        """Calculate overall evidence grade from documents."""
        if not documents:
            return None

        grade_counts = {"A": 0, "B": 0, "C": 0}
        for doc in documents:
            if doc.evidence_grade:
                grade_counts[doc.evidence_grade.value] += 1

        # If majority is A, overall is A
        total = sum(grade_counts.values())
        if total == 0:
            return EvidenceGrade.C

        if grade_counts["A"] / total >= 0.5:
            return EvidenceGrade.A
        elif (grade_counts["A"] + grade_counts["B"]) / total >= 0.5:
            return EvidenceGrade.B
        else:
            return EvidenceGrade.C

    def _calculate_confidence(
        self,
        documents: list[Document],
        synthesis: ResearchSynthesis,
    ) -> float:
        """Calculate confidence score for results."""
        if not documents:
            return 0.1

        # Base on document count and evidence quality
        doc_score = min(len(documents) / 10, 1.0) * 0.3

        # Evidence grade score
        grade_scores = {"A": 1.0, "B": 0.7, "C": 0.4}
        grade_total = sum(
            grade_scores.get(d.evidence_grade.value if d.evidence_grade else "C", 0.4)
            for d in documents
        )
        grade_score = (grade_total / len(documents)) * 0.4

        # Finding consistency
        finding_score = min(len(synthesis.key_findings) / 5, 1.0) * 0.3

        return min(doc_score + grade_score + finding_score, 1.0)

    async def close(self):
        """Close all clients."""
        await self.pubmed_client.close()
        await self.trials_client.close()


# =============================================================================
# Factory
# =============================================================================


def create_research_agent() -> ResearchAgent:
    """Create configured research agent."""
    return ResearchAgent()
