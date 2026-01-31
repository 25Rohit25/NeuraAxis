"""
NEURAXIS - Knowledge Base Service
Medical guidelines and custom knowledge base management
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.agents.research_schemas import (
    Author,
    Document,
    DocumentChunk,
    EvidenceGrade,
    IndexingJob,
    SourceType,
    StudyType,
)
from app.core.config import settings
from app.services.vector_store import (
    DocumentChunker,
    EmbeddingService,
    get_embedding_service,
    get_vector_store,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Medical Guidelines Database
# =============================================================================

# Pre-loaded medical guidelines for common conditions
MEDICAL_GUIDELINES = [
    {
        "id": "guideline:acc-aha-hypertension-2017",
        "title": "2017 ACC/AHA Guideline for the Prevention, Detection, Evaluation, and Management of High Blood Pressure in Adults",
        "source": "American College of Cardiology / American Heart Association",
        "year": 2017,
        "category": "Cardiovascular",
        "summary": """
        Key recommendations:
        - BP categories: Normal (<120/<80), Elevated (120-129/<80), Stage 1 (130-139/80-89), Stage 2 (≥140/≥90)
        - First-line medications: Thiazide diuretics, CCBs, ACE inhibitors, or ARBs
        - Initial therapy with 2 drugs recommended for Stage 2 hypertension
        - Target BP <130/80 for most adults
        - Lifestyle modifications for all patients with elevated BP
        """,
        "mesh_terms": ["Hypertension", "Blood Pressure", "Antihypertensive Agents"],
    },
    {
        "id": "guideline:ada-diabetes-2024",
        "title": "Standards of Care in Diabetes—2024",
        "source": "American Diabetes Association",
        "year": 2024,
        "category": "Endocrine",
        "summary": """
        Key recommendations:
        - A1C target <7% for most adults, individualized based on patient factors
        - Metformin remains first-line pharmacotherapy for type 2 diabetes
        - GLP-1 RA or SGLT2 inhibitors preferred for patients with ASCVD, HF, or CKD
        - Lifestyle intervention essential for all patients
        - Comprehensive cardiovascular risk reduction
        - Regular screening for complications
        """,
        "mesh_terms": ["Diabetes Mellitus", "Glycated Hemoglobin", "Hypoglycemic Agents"],
    },
    {
        "id": "guideline:gina-asthma-2023",
        "title": "Global Strategy for Asthma Management and Prevention (GINA 2023)",
        "source": "Global Initiative for Asthma",
        "year": 2023,
        "category": "Pulmonary",
        "summary": """
        Key recommendations:
        - Track 1 (preferred): As-needed low-dose ICS-formoterol for Steps 1-2
        - Track 2: SABA-only relief not recommended due to increased risk
        - Assess asthma control using validated tools (ACQ, ACT)
        - Step up if uncontrolled, step down after 3 months of good control
        - Biologic therapy for severe uncontrolled asthma
        """,
        "mesh_terms": ["Asthma", "Anti-Asthmatic Agents", "Bronchodilator Agents"],
    },
    {
        "id": "guideline:esc-heart-failure-2021",
        "title": "2021 ESC Guidelines for the Diagnosis and Treatment of Acute and Chronic Heart Failure",
        "source": "European Society of Cardiology",
        "year": 2021,
        "category": "Cardiovascular",
        "summary": """
        Key recommendations:
        - HFrEF quadruple therapy: ACEi/ARNI, beta-blocker, MRA, SGLT2 inhibitor
        - Early initiation of therapy recommended
        - Device therapy (ICD, CRT) based on EF and QRS duration
        - Multidisciplinary heart failure programs
        - Cardiac rehabilitation for all stable HF patients
        - Diuretics for congestion relief
        """,
        "mesh_terms": [
            "Heart Failure",
            "Ventricular Dysfunction",
            "Cardiac Resynchronization Therapy",
        ],
    },
    {
        "id": "guideline:aha-stroke-2019",
        "title": "Guidelines for the Early Management of Patients With Acute Ischemic Stroke: 2019 Update",
        "source": "American Heart Association / American Stroke Association",
        "year": 2019,
        "category": "Neurology",
        "summary": """
        Key recommendations:
        - IV alteplase within 4.5 hours of symptom onset
        - Mechanical thrombectomy for large vessel occlusion up to 24 hours in select patients
        - Admit to stroke unit for monitoring
        - Early mobilization
        - Swallow screening before oral intake
        - Secondary prevention initiated before discharge
        """,
        "mesh_terms": ["Stroke", "Thrombolytic Therapy", "Thrombectomy"],
    },
    {
        "id": "guideline:nice-depression-2022",
        "title": "Depression in Adults: Treatment and Management (NICE NG222)",
        "source": "National Institute for Health and Care Excellence",
        "year": 2022,
        "category": "Psychiatry",
        "summary": """
        Key recommendations:
        - Discuss treatment options including watchful waiting, self-help, psychological therapy, medication
        - For less severe depression: consider active monitoring, low-intensity interventions
        - For more severe depression: high-intensity psychological intervention or antidepressant
        - SSRIs generally first-line if medication indicated
        - Combination therapy for severe or treatment-resistant depression
        - Regular review and monitoring
        """,
        "mesh_terms": ["Depressive Disorder", "Antidepressive Agents", "Psychotherapy"],
    },
]


# =============================================================================
# Knowledge Base Service
# =============================================================================


class KnowledgeBaseService:
    """
    Service for managing medical knowledge base.

    Features:
    - Pre-loaded medical guidelines
    - Custom document ingestion
    - Vector embedding and indexing
    - Semantic search
    """

    def __init__(self):
        self.embedding_service = get_embedding_service()
        self.vector_store = get_vector_store()
        self.chunker = DocumentChunker(chunk_size=400, chunk_overlap=50)

        self._guidelines_indexed = False

        logger.info("KnowledgeBaseService initialized")

    def get_guidelines(self) -> list[Document]:
        """Get all pre-loaded medical guidelines as Documents."""
        documents = []

        for g in MEDICAL_GUIDELINES:
            doc = Document(
                id=g["id"],
                source_type=SourceType.GUIDELINE,
                title=g["title"],
                abstract=g["summary"].strip(),
                content=g["summary"].strip(),
                authors=[Author(name=g["source"])],
                publication_date=datetime(g["year"], 1, 1),
                study_type=StudyType.GUIDELINE,
                evidence_grade=EvidenceGrade.A,  # Guidelines are typically high evidence
                mesh_terms=g.get("mesh_terms", []),
                keywords=[g["category"]],
            )
            documents.append(doc)

        return documents

    def search_guidelines_by_keyword(
        self,
        keywords: list[str],
        max_results: int = 5,
    ) -> list[Document]:
        """
        Search guidelines by keyword matching.

        Args:
            keywords: Keywords to search for
            max_results: Maximum results to return

        Returns:
            Matching guideline documents
        """
        keywords_lower = [k.lower() for k in keywords]
        guidelines = self.get_guidelines()

        scored = []
        for doc in guidelines:
            score = 0

            # Check title
            for kw in keywords_lower:
                if kw in doc.title.lower():
                    score += 3

            # Check content
            for kw in keywords_lower:
                if kw in (doc.content or "").lower():
                    score += 1

            # Check MeSH terms
            for kw in keywords_lower:
                for mesh in doc.mesh_terms:
                    if kw in mesh.lower():
                        score += 2

            if score > 0:
                doc.relevance_score = score / 10  # Normalize
                scored.append(doc)

        # Sort by score
        scored.sort(key=lambda d: d.relevance_score, reverse=True)

        return scored[:max_results]

    async def index_guidelines(self) -> int:
        """
        Index all guidelines in vector store.

        Returns:
            Number of vectors indexed
        """
        if self._guidelines_indexed:
            logger.info("Guidelines already indexed")
            return 0

        guidelines = self.get_guidelines()
        total_chunks = 0

        for doc in guidelines:
            chunks = self.chunker.chunk_document(doc)

            if chunks:
                # Generate embeddings
                texts = [c.content for c in chunks]
                embeddings = self.embedding_service.embed_batch(texts)

                # Upsert to vector store
                await self.vector_store.upsert(
                    chunks=chunks,
                    embeddings=embeddings,
                    namespace="guidelines",
                )

                total_chunks += len(chunks)

        self._guidelines_indexed = True
        logger.info(f"Indexed {total_chunks} guideline chunks")

        return total_chunks

    async def index_document(
        self,
        document: Document,
        namespace: str = "custom",
    ) -> int:
        """
        Index a custom document.

        Args:
            document: Document to index
            namespace: Vector store namespace

        Returns:
            Number of chunks indexed
        """
        chunks = self.chunker.chunk_document(document)

        if not chunks:
            return 0

        # Generate embeddings
        texts = [c.content for c in chunks]
        embeddings = self.embedding_service.embed_batch(texts)

        # Upsert to vector store
        await self.vector_store.upsert(
            chunks=chunks,
            embeddings=embeddings,
            namespace=namespace,
        )

        logger.info(f"Indexed {len(chunks)} chunks for document: {document.id}")

        return len(chunks)

    async def search(
        self,
        query: str,
        namespace: str = "guidelines",
        top_k: int = 5,
    ) -> list[Document]:
        """
        Semantic search in knowledge base.

        Args:
            query: Search query
            namespace: Namespace to search
            top_k: Number of results

        Returns:
            Matching documents
        """
        # Generate query embedding
        query_embedding = self.embedding_service.embed_text(query)

        # Search vector store
        results = await self.vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k,
            namespace=namespace,
        )

        # Convert to documents
        documents = []
        seen_doc_ids = set()

        for result in results:
            # Extract document ID from chunk ID
            doc_id = result.metadata.get("document_id") or result.id.split(":chunk:")[0]

            if doc_id in seen_doc_ids:
                continue
            seen_doc_ids.add(doc_id)

            # Build document from metadata
            doc = Document(
                id=doc_id,
                source_type=SourceType(result.metadata.get("source_type", "knowledge_base")),
                title=result.metadata.get("title", "Unknown"),
                content=result.content,
                snippet=result.content[:300] if result.content else None,
                relevance_score=result.score,
                evidence_grade=EvidenceGrade(result.metadata.get("evidence_grade", "C"))
                if result.metadata.get("evidence_grade")
                else EvidenceGrade.C,
            )

            documents.append(doc)

        return documents

    async def create_indexing_job(
        self,
        source_type: str,
        documents: list[Document],
    ) -> IndexingJob:
        """
        Create a background indexing job.

        Args:
            source_type: Type of source being indexed
            documents: Documents to index

        Returns:
            IndexingJob tracking object
        """
        job_id = str(uuid4())

        job = IndexingJob(
            job_id=job_id,
            status="pending",
            source_type=SourceType(source_type),
            documents_total=len(documents),
            started_at=datetime.now(),
        )

        # In production, this would be stored in Redis/database
        # and processed by a background worker

        return job


# =============================================================================
# Factory
# =============================================================================

_kb_service: KnowledgeBaseService | None = None


def get_knowledge_base_service() -> KnowledgeBaseService:
    """Get knowledge base service singleton."""
    global _kb_service
    if _kb_service is None:
        _kb_service = KnowledgeBaseService()
    return _kb_service
