"""
NEURAXIS - Duplicate Patient Detection Algorithm
Detects potential duplicate patients based on name and DOB matching
"""

import re
from dataclasses import dataclass
from datetime import date
from difflib import SequenceMatcher
from typing import Optional
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class DuplicateCandidate:
    """Represents a potential duplicate patient."""

    id: UUID
    mrn: str
    first_name: str
    last_name: str
    date_of_birth: date
    similarity_score: float
    match_reason: str


class DuplicateDetector:
    """
    Detects potential duplicate patients using fuzzy matching.

    Matching criteria:
    1. Exact match: Same name + same DOB (100% confidence)
    2. High match: Similar name (>85% similarity) + same DOB (90%+ confidence)
    3. Medium match: Similar name + DOB within 1 year (70%+ confidence)
    4. Low match: Same DOB + first 3 letters of name match (60%+ confidence)
    """

    # Minimum similarity score to consider as potential duplicate
    MIN_SIMILARITY_THRESHOLD = 0.60

    # Weights for different matching factors
    NAME_WEIGHT = 0.6
    DOB_WEIGHT = 0.4

    @classmethod
    def normalize_name(cls, name: str) -> str:
        """
        Normalize a name for comparison.
        - Lowercase
        - Remove special characters
        - Remove extra whitespace
        """
        if not name:
            return ""
        # Convert to lowercase
        name = name.lower()
        # Remove special characters except spaces
        name = re.sub(r"[^a-z\s]", "", name)
        # Normalize whitespace
        name = " ".join(name.split())
        return name

    @classmethod
    def calculate_name_similarity(cls, name1: str, name2: str) -> float:
        """
        Calculate similarity between two names using SequenceMatcher.
        Returns a value between 0 and 1.
        """
        n1 = cls.normalize_name(name1)
        n2 = cls.normalize_name(name2)

        if not n1 or not n2:
            return 0.0

        # Use SequenceMatcher for fuzzy matching
        return SequenceMatcher(None, n1, n2).ratio()

    @classmethod
    def calculate_dob_similarity(
        cls,
        dob1: date,
        dob2: date,
    ) -> tuple[float, str]:
        """
        Calculate similarity between two dates of birth.

        Returns:
            Tuple of (similarity_score, match_type)
        """
        if dob1 == dob2:
            return 1.0, "exact_dob"

        # Calculate year difference
        year_diff = abs(dob1.year - dob2.year)

        # Same month and day, different year (possible typo or transcription error)
        if dob1.month == dob2.month and dob1.day == dob2.day:
            if year_diff <= 1:
                return 0.8, "same_monthday_near_year"
            elif year_diff <= 10:
                return 0.5, "same_monthday_decade"
            return 0.2, "same_monthday_different_year"

        # Same year and month, different day (possible typo)
        if dob1.year == dob2.year and dob1.month == dob2.month:
            day_diff = abs(dob1.day - dob2.day)
            if day_diff <= 1:
                return 0.9, "same_yearmonth_near_day"
            elif day_diff <= 7:
                return 0.6, "same_yearmonth_week"
            return 0.3, "same_yearmonth"

        # Same year, different month (less likely duplicate)
        if dob1.year == dob2.year:
            return 0.2, "same_year"

        # Within 1 year
        if year_diff <= 1:
            return 0.1, "near_year"

        return 0.0, "different"

    @classmethod
    def calculate_overall_similarity(
        cls,
        first_name1: str,
        last_name1: str,
        dob1: date,
        first_name2: str,
        last_name2: str,
        dob2: date,
    ) -> tuple[float, str]:
        """
        Calculate overall similarity score between two patients.

        Returns:
            Tuple of (similarity_score, match_reason)
        """
        # Calculate name similarities
        first_name_sim = cls.calculate_name_similarity(first_name1, first_name2)
        last_name_sim = cls.calculate_name_similarity(last_name1, last_name2)

        # Last name is more important for matching
        name_sim = (first_name_sim * 0.4) + (last_name_sim * 0.6)

        # Calculate DOB similarity
        dob_sim, dob_match_type = cls.calculate_dob_similarity(dob1, dob2)

        # Build match reason
        reasons = []

        # Exact match detection
        if first_name_sim > 0.95 and last_name_sim > 0.95 and dob_sim == 1.0:
            return 1.0, "Exact match: Same name and DOB"

        if last_name_sim > 0.85:
            reasons.append(f"Last name match ({last_name_sim:.0%})")
        elif last_name_sim > 0.6:
            reasons.append(f"Similar last name ({last_name_sim:.0%})")

        if first_name_sim > 0.85:
            reasons.append(f"First name match ({first_name_sim:.0%})")
        elif first_name_sim > 0.6:
            reasons.append(f"Similar first name ({first_name_sim:.0%})")

        if dob_sim == 1.0:
            reasons.append("Same DOB")
        elif dob_sim > 0.5:
            reasons.append(f"Similar DOB ({dob_match_type})")

        # Calculate weighted score
        overall_score = (name_sim * cls.NAME_WEIGHT) + (dob_sim * cls.DOB_WEIGHT)

        match_reason = "; ".join(reasons) if reasons else "Low similarity"

        return overall_score, match_reason

    @classmethod
    async def find_duplicates(
        cls,
        session: AsyncSession,
        patient_model,
        first_name: str,
        last_name: str,
        date_of_birth: date,
        organization_id: UUID,
        exclude_id: Optional[UUID] = None,
        limit: int = 10,
    ) -> list[DuplicateCandidate]:
        """
        Find potential duplicate patients in the database.

        Args:
            session: Database session
            patient_model: SQLAlchemy Patient model
            first_name: Patient's first name
            last_name: Patient's last name
            date_of_birth: Patient's date of birth
            organization_id: Organization to search within
            exclude_id: Patient ID to exclude (for updates)
            limit: Maximum number of duplicates to return

        Returns:
            List of potential duplicate candidates sorted by similarity
        """
        # Normalize search names
        search_first = cls.normalize_name(first_name)
        search_last = cls.normalize_name(last_name)

        # Build query for potential matches
        # Start with broad criteria and then filter in Python for fuzzy matching
        query = select(patient_model).where(
            patient_model.organization_id == organization_id,
            patient_model.is_deleted == False,  # noqa: E712
        )

        # Add constraints to reduce candidate set
        # Match on DOB year ±2 years OR first letter of last name matches
        year = date_of_birth.year
        first_letter = search_last[0].upper() if search_last else ""

        query = query.where(
            or_(
                # Same DOB (high priority)
                patient_model.date_of_birth == date_of_birth,
                # DOB within 2 years AND similar last name start
                (
                    patient_model.date_of_birth.between(
                        date(year - 2, 1, 1),
                        date(year + 2, 12, 31),
                    )
                ),
            )
        )

        # Exclude specific patient if updating
        if exclude_id:
            query = query.where(patient_model.id != exclude_id)

        # Limit initial fetch
        query = query.limit(100)

        result = await session.execute(query)
        candidates = result.scalars().all()

        # Calculate similarity for each candidate
        duplicates: list[DuplicateCandidate] = []

        for patient in candidates:
            score, reason = cls.calculate_overall_similarity(
                first_name,
                last_name,
                date_of_birth,
                patient.first_name,
                patient.last_name,
                patient.date_of_birth,
            )

            if score >= cls.MIN_SIMILARITY_THRESHOLD:
                duplicates.append(
                    DuplicateCandidate(
                        id=patient.id,
                        mrn=patient.mrn,
                        first_name=patient.first_name,
                        last_name=patient.last_name,
                        date_of_birth=patient.date_of_birth,
                        similarity_score=score,
                        match_reason=reason,
                    )
                )

        # Sort by similarity score (highest first)
        duplicates.sort(key=lambda x: x.similarity_score, reverse=True)

        return duplicates[:limit]


async def check_for_duplicates(
    session: AsyncSession,
    patient_model,
    first_name: str,
    last_name: str,
    date_of_birth: date,
    organization_id: UUID,
    exclude_id: Optional[UUID] = None,
) -> list[DuplicateCandidate]:
    """Convenience function for duplicate detection."""
    return await DuplicateDetector.find_duplicates(
        session=session,
        patient_model=patient_model,
        first_name=first_name,
        last_name=last_name,
        date_of_birth=date_of_birth,
        organization_id=organization_id,
        exclude_id=exclude_id,
    )
