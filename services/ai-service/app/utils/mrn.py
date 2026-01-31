"""
NEURAXIS - MRN (Medical Record Number) Generation Utility
Generates unique, formatted medical record numbers
"""

import random
import string
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class MRNGenerator:
    """
    Medical Record Number generator.

    Format: NRX-YYYY-XXXXXXXX
    - NRX: NEURAXIS prefix
    - YYYY: Year of registration
    - XXXXXXXX: 8-character alphanumeric (uppercase letters + digits)

    Example: NRX-2026-A3B7C9D2
    """

    PREFIX = "NRX"
    YEAR_FORMAT = "%Y"
    RANDOM_LENGTH = 8
    # Exclude similar-looking characters: 0/O, 1/I/L, 5/S
    ALLOWED_CHARS = "23467899ABCDEFGHJKMNPQRTUVWXYZ"

    @classmethod
    def generate(cls, year: Optional[int] = None) -> str:
        """
        Generate a new MRN.

        Args:
            year: Optional year. Defaults to current year.

        Returns:
            Formatted MRN string.
        """
        if year is None:
            year = datetime.now().year

        random_part = "".join(random.choices(cls.ALLOWED_CHARS, k=cls.RANDOM_LENGTH))

        return f"{cls.PREFIX}-{year}-{random_part}"

    @classmethod
    async def generate_unique(
        cls,
        session: AsyncSession,
        patient_model,
        max_attempts: int = 10,
    ) -> str:
        """
        Generate a unique MRN that doesn't exist in the database.

        Args:
            session: Database session
            patient_model: SQLAlchemy Patient model class
            max_attempts: Maximum generation attempts

        Returns:
            Unique MRN string

        Raises:
            RuntimeError: If unable to generate unique MRN after max attempts
        """
        for _ in range(max_attempts):
            mrn = cls.generate()

            # Check if MRN exists
            result = await session.execute(
                select(patient_model.id).where(patient_model.mrn == mrn).limit(1)
            )
            existing = result.scalar_one_or_none()

            if existing is None:
                return mrn

        raise RuntimeError(f"Failed to generate unique MRN after {max_attempts} attempts")

    @classmethod
    def validate(cls, mrn: str) -> bool:
        """
        Validate MRN format.

        Args:
            mrn: MRN string to validate

        Returns:
            True if valid format, False otherwise
        """
        if not mrn:
            return False

        parts = mrn.split("-")
        if len(parts) != 3:
            return False

        prefix, year, random_part = parts

        # Check prefix
        if prefix != cls.PREFIX:
            return False

        # Check year (should be 4 digits)
        if not year.isdigit() or len(year) != 4:
            return False

        # Check year range (reasonable bounds)
        year_int = int(year)
        if year_int < 2020 or year_int > 2100:
            return False

        # Check random part
        if len(random_part) != cls.RANDOM_LENGTH:
            return False

        if not all(c in cls.ALLOWED_CHARS for c in random_part):
            return False

        return True

    @classmethod
    def parse(cls, mrn: str) -> dict:
        """
        Parse MRN into components.

        Args:
            mrn: MRN string to parse

        Returns:
            Dictionary with prefix, year, and random_part

        Raises:
            ValueError: If MRN format is invalid
        """
        if not cls.validate(mrn):
            raise ValueError(f"Invalid MRN format: {mrn}")

        parts = mrn.split("-")
        return {
            "prefix": parts[0],
            "year": int(parts[1]),
            "random_part": parts[2],
            "full": mrn,
        }


def generate_mrn() -> str:
    """Convenience function to generate an MRN."""
    return MRNGenerator.generate()


async def generate_unique_mrn(session: AsyncSession, patient_model) -> str:
    """Convenience function to generate a unique MRN."""
    return await MRNGenerator.generate_unique(session, patient_model)
