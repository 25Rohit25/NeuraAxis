"""
NEURAXIS - ICD-10 Code Validator
Validates and looks up ICD-10 diagnosis codes
"""

import json
from functools import lru_cache
from pathlib import Path
from typing import NamedTuple


class ICD10Code(NamedTuple):
    """Validated ICD-10 code."""

    code: str
    description: str
    category: str
    is_billable: bool


# Common ICD-10 codes for quick validation without full database
COMMON_ICD10_CODES: dict[str, str] = {
    # Cardiovascular
    "I21.0": "ST elevation (STEMI) myocardial infarction of anterior wall",
    "I21.1": "ST elevation (STEMI) myocardial infarction of inferior wall",
    "I21.2": "ST elevation (STEMI) myocardial infarction of other sites",
    "I21.3": "ST elevation (STEMI) myocardial infarction of unspecified site",
    "I21.4": "Non-ST elevation (NSTEMI) myocardial infarction",
    "I20.0": "Unstable angina",
    "I20.9": "Angina pectoris, unspecified",
    "I10": "Essential (primary) hypertension",
    "I25.10": "Atherosclerotic heart disease of native coronary artery without angina pectoris",
    "I50.9": "Heart failure, unspecified",
    "I48.91": "Unspecified atrial fibrillation",
    # Respiratory
    "J06.9": "Acute upper respiratory infection, unspecified",
    "J18.9": "Pneumonia, unspecified organism",
    "J44.1": "Chronic obstructive pulmonary disease with acute exacerbation",
    "J45.20": "Mild intermittent asthma, uncomplicated",
    "J45.50": "Severe persistent asthma, uncomplicated",
    "J96.00": "Acute respiratory failure, unspecified whether with hypoxia or hypercapnia",
    # Neurological
    "G43.909": "Migraine, unspecified, not intractable, without status migrainosus",
    "G43.109": "Migraine with aura, not intractable, without status migrainosus",
    "G43.009": "Migraine without aura, not intractable, without status migrainosus",
    "G44.209": "Tension-type headache, unspecified, not intractable",
    "G40.909": "Epilepsy, unspecified, not intractable, without status epilepticus",
    "I63.9": "Cerebral infarction, unspecified",
    "I61.9": "Nontraumatic intracerebral hemorrhage, unspecified",
    # Gastrointestinal
    "K21.0": "Gastro-esophageal reflux disease with esophagitis",
    "K25.9": "Gastric ulcer, unspecified, without hemorrhage or perforation",
    "K35.80": "Unspecified acute appendicitis",
    "K80.20": "Calculus of gallbladder without cholecystitis without obstruction",
    "K85.90": "Acute pancreatitis, unspecified, without necrosis or infection",
    "K50.90": "Crohn's disease, unspecified, without complications",
    "K51.90": "Ulcerative colitis, unspecified, without complications",
    # Infectious
    "A41.9": "Sepsis, unspecified organism",
    "A49.9": "Bacterial infection, unspecified",
    "B34.9": "Viral infection, unspecified",
    "N39.0": "Urinary tract infection, site not specified",
    "J02.9": "Acute pharyngitis, unspecified",
    # Endocrine
    "E11.9": "Type 2 diabetes mellitus without complications",
    "E10.9": "Type 1 diabetes mellitus without complications",
    "E03.9": "Hypothyroidism, unspecified",
    "E05.90": "Thyrotoxicosis, unspecified without thyrotoxic crisis or storm",
    # Musculoskeletal
    "M54.5": "Low back pain",
    "M79.3": "Panniculitis, unspecified",
    "M25.50": "Pain in unspecified joint",
    # Psychiatric
    "F32.9": "Major depressive disorder, single episode, unspecified",
    "F41.1": "Generalized anxiety disorder",
    "F41.9": "Anxiety disorder, unspecified",
    # Symptoms and Signs
    "R07.9": "Chest pain, unspecified",
    "R51.9": "Headache, unspecified",
    "R10.9": "Unspecified abdominal pain",
    "R50.9": "Fever, unspecified",
    "R06.00": "Dyspnea, unspecified",
    "R42": "Dizziness and giddiness",
    "R55": "Syncope and collapse",
    "R11.10": "Vomiting, unspecified",
    "R11.0": "Nausea",
}


# Code format patterns for validation
ICD10_PATTERNS = [
    r"^[A-Z]\d{2}$",  # A00-Z99 (category)
    r"^[A-Z]\d{2}\.\d$",  # A00.0-Z99.9 (subcategory)
    r"^[A-Z]\d{2}\.\d{2}$",  # A00.00-Z99.99 (code)
    r"^[A-Z]\d{2}\.\d{3}$",  # A00.000-Z99.999 (extension)
    r"^[A-Z]\d{2}\.\d{4}$",  # A00.0000-Z99.9999 (full extension)
]


class ICD10Validator:
    """Validates and provides ICD-10 code information."""

    def __init__(self, codes_file: str | None = None):
        """
        Initialize validator with optional external codes file.

        Args:
            codes_file: Path to JSON file with additional ICD-10 codes
        """
        self.codes = dict(COMMON_ICD10_CODES)

        if codes_file and Path(codes_file).exists():
            self._load_external_codes(codes_file)

    def _load_external_codes(self, codes_file: str):
        """Load additional codes from external file."""
        try:
            with open(codes_file, "r") as f:
                external_codes = json.load(f)
                self.codes.update(external_codes)
        except Exception as e:
            print(f"Warning: Could not load external ICD-10 codes: {e}")

    def validate_format(self, code: str) -> bool:
        """
        Validate ICD-10 code format.

        Args:
            code: ICD-10 code to validate

        Returns:
            True if format is valid
        """
        import re

        if not code:
            return False

        code = code.upper().strip()

        for pattern in ICD10_PATTERNS:
            if re.match(pattern, code):
                return True

        return False

    def validate_code(self, code: str) -> tuple[bool, str | None]:
        """
        Validate ICD-10 code exists in database.

        Args:
            code: ICD-10 code to validate

        Returns:
            Tuple of (is_valid, description or error message)
        """
        if not code:
            return False, "Empty code provided"

        code = code.upper().strip()

        # Check format first
        if not self.validate_format(code):
            return False, f"Invalid ICD-10 code format: {code}"

        # Look up in database
        if code in self.codes:
            return True, self.codes[code]

        # Check for parent code (category level)
        parent_code = code.split(".")[0] if "." in code else code
        if parent_code in self.codes:
            return True, f"Valid code under category: {self.codes[parent_code]}"

        # Code format is valid but not in our database
        return True, f"Code format valid but not in local database: {code}"

    def get_code_info(self, code: str) -> ICD10Code | None:
        """
        Get full information for an ICD-10 code.

        Args:
            code: ICD-10 code

        Returns:
            ICD10Code named tuple or None if not found
        """
        code = code.upper().strip()

        if code not in self.codes:
            return None

        # Determine category from first character
        category_map = {
            "A": "Infectious diseases",
            "B": "Infectious diseases",
            "C": "Neoplasms",
            "D": "Blood disorders",
            "E": "Endocrine disorders",
            "F": "Mental disorders",
            "G": "Nervous system",
            "H": "Eye and ear",
            "I": "Circulatory system",
            "J": "Respiratory system",
            "K": "Digestive system",
            "L": "Skin disorders",
            "M": "Musculoskeletal",
            "N": "Genitourinary",
            "O": "Pregnancy",
            "P": "Perinatal",
            "Q": "Congenital",
            "R": "Symptoms and signs",
            "S": "Injury",
            "T": "Injury",
            "U": "Special purposes",
            "V": "External causes",
            "W": "External causes",
            "X": "External causes",
            "Y": "External causes",
            "Z": "Health status",
        }

        category = category_map.get(code[0], "Unknown")

        # Billable codes typically have decimal point
        is_billable = "." in code and len(code.split(".")[1]) >= 1

        return ICD10Code(
            code=code, description=self.codes[code], category=category, is_billable=is_billable
        )

    def search_codes(self, query: str, limit: int = 10) -> list[ICD10Code]:
        """
        Search for ICD-10 codes by description.

        Args:
            query: Search term
            limit: Maximum results to return

        Returns:
            List of matching ICD10Code entries
        """
        query = query.lower()
        results = []

        for code, description in self.codes.items():
            if query in description.lower() or query in code.lower():
                info = self.get_code_info(code)
                if info:
                    results.append(info)

                if len(results) >= limit:
                    break

        return results

    def suggest_code(self, diagnosis: str) -> list[ICD10Code]:
        """
        Suggest ICD-10 codes for a diagnosis description.

        Args:
            diagnosis: Free-text diagnosis

        Returns:
            List of suggested ICD10Code entries
        """
        # Simple keyword matching - in production, use semantic similarity
        keywords = diagnosis.lower().split()

        scores: dict[str, int] = {}

        for code, description in self.codes.items():
            desc_lower = description.lower()
            score = sum(1 for kw in keywords if kw in desc_lower)
            if score > 0:
                scores[code] = score

        # Sort by score and return top matches
        sorted_codes = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        results = []
        for code, _ in sorted_codes[:5]:
            info = self.get_code_info(code)
            if info:
                results.append(info)

        return results


# Global validator instance
@lru_cache()
def get_icd10_validator() -> ICD10Validator:
    """Get cached ICD-10 validator instance."""
    return ICD10Validator()


def validate_diagnosis_codes(diagnoses: list[dict]) -> list[dict]:
    """
    Validate ICD-10 codes in a list of diagnoses.

    Args:
        diagnoses: List of diagnosis dictionaries with 'icd10_code' field

    Returns:
        List with added validation info
    """
    validator = get_icd10_validator()

    for diagnosis in diagnoses:
        code = diagnosis.get("icd10_code", "")
        is_valid, message = validator.validate_code(code)

        diagnosis["icd10_valid"] = is_valid
        diagnosis["icd10_validation_message"] = message

        if is_valid:
            info = validator.get_code_info(code)
            if info:
                diagnosis["icd10_category"] = info.category
                diagnosis["icd10_billable"] = info.is_billable

    return diagnoses
