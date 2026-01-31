"""
NEURAXIS - Medication Cost Estimation Service
Drug pricing and insurance coverage estimation
"""

import logging
from dataclasses import dataclass

from app.agents.treatment_schemas import (
    CoverageStatus,
    InsuranceCoverage,
    MedicationCost,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Drug Pricing Database
# =============================================================================


@dataclass
class DrugPricing:
    """Drug pricing information."""

    generic_name: str
    brand_names: list[str]
    generic_available: bool
    generic_30_day_cost: float | None  # AWP estimate
    brand_30_day_cost: float | None
    typical_copay_generic: float | None
    typical_copay_brand: float | None
    common_tier: int  # 1-5 formulary tier


# Pricing data (simplified - would use real drug pricing API in production)
DRUG_PRICING_DB = {
    "metformin": DrugPricing(
        generic_name="metformin",
        brand_names=["Glucophage", "Glucophage XR", "Fortamet"],
        generic_available=True,
        generic_30_day_cost=15.00,
        brand_30_day_cost=150.00,
        typical_copay_generic=5.00,
        typical_copay_brand=35.00,
        common_tier=1,
    ),
    "lisinopril": DrugPricing(
        generic_name="lisinopril",
        brand_names=["Zestril", "Prinivil"],
        generic_available=True,
        generic_30_day_cost=12.00,
        brand_30_day_cost=120.00,
        typical_copay_generic=5.00,
        typical_copay_brand=30.00,
        common_tier=1,
    ),
    "atorvastatin": DrugPricing(
        generic_name="atorvastatin",
        brand_names=["Lipitor"],
        generic_available=True,
        generic_30_day_cost=20.00,
        brand_30_day_cost=400.00,
        typical_copay_generic=10.00,
        typical_copay_brand=60.00,
        common_tier=1,
    ),
    "rosuvastatin": DrugPricing(
        generic_name="rosuvastatin",
        brand_names=["Crestor"],
        generic_available=True,
        generic_30_day_cost=25.00,
        brand_30_day_cost=350.00,
        typical_copay_generic=10.00,
        typical_copay_brand=60.00,
        common_tier=1,
    ),
    "amlodipine": DrugPricing(
        generic_name="amlodipine",
        brand_names=["Norvasc"],
        generic_available=True,
        generic_30_day_cost=10.00,
        brand_30_day_cost=150.00,
        typical_copay_generic=5.00,
        typical_copay_brand=35.00,
        common_tier=1,
    ),
    "omeprazole": DrugPricing(
        generic_name="omeprazole",
        brand_names=["Prilosec"],
        generic_available=True,
        generic_30_day_cost=15.00,
        brand_30_day_cost=200.00,
        typical_copay_generic=5.00,
        typical_copay_brand=40.00,
        common_tier=1,
    ),
    "gabapentin": DrugPricing(
        generic_name="gabapentin",
        brand_names=["Neurontin"],
        generic_available=True,
        generic_30_day_cost=20.00,
        brand_30_day_cost=250.00,
        typical_copay_generic=10.00,
        typical_copay_brand=50.00,
        common_tier=1,
    ),
    "sertraline": DrugPricing(
        generic_name="sertraline",
        brand_names=["Zoloft"],
        generic_available=True,
        generic_30_day_cost=15.00,
        brand_30_day_cost=300.00,
        typical_copay_generic=5.00,
        typical_copay_brand=50.00,
        common_tier=1,
    ),
    "levothyroxine": DrugPricing(
        generic_name="levothyroxine",
        brand_names=["Synthroid", "Levoxyl"],
        generic_available=True,
        generic_30_day_cost=12.00,
        brand_30_day_cost=100.00,
        typical_copay_generic=5.00,
        typical_copay_brand=25.00,
        common_tier=1,
    ),
    "amoxicillin": DrugPricing(
        generic_name="amoxicillin",
        brand_names=["Amoxil"],
        generic_available=True,
        generic_30_day_cost=10.00,
        brand_30_day_cost=80.00,
        typical_copay_generic=5.00,
        typical_copay_brand=20.00,
        common_tier=1,
    ),
    "azithromycin": DrugPricing(
        generic_name="azithromycin",
        brand_names=["Zithromax", "Z-Pak"],
        generic_available=True,
        generic_30_day_cost=15.00,
        brand_30_day_cost=100.00,
        typical_copay_generic=10.00,
        typical_copay_brand=30.00,
        common_tier=1,
    ),
    "prednisone": DrugPricing(
        generic_name="prednisone",
        brand_names=["Deltasone"],
        generic_available=True,
        generic_30_day_cost=8.00,
        brand_30_day_cost=50.00,
        typical_copay_generic=5.00,
        typical_copay_brand=15.00,
        common_tier=1,
    ),
    # Brand-only or expensive medications
    "eliquis": DrugPricing(
        generic_name="apixaban",
        brand_names=["Eliquis"],
        generic_available=False,
        generic_30_day_cost=None,
        brand_30_day_cost=550.00,
        typical_copay_generic=None,
        typical_copay_brand=75.00,
        common_tier=3,
    ),
    "xarelto": DrugPricing(
        generic_name="rivaroxaban",
        brand_names=["Xarelto"],
        generic_available=False,
        generic_30_day_cost=None,
        brand_30_day_cost=520.00,
        typical_copay_generic=None,
        typical_copay_brand=75.00,
        common_tier=3,
    ),
    "jardiance": DrugPricing(
        generic_name="empagliflozin",
        brand_names=["Jardiance"],
        generic_available=False,
        generic_30_day_cost=None,
        brand_30_day_cost=580.00,
        typical_copay_generic=None,
        typical_copay_brand=80.00,
        common_tier=3,
    ),
    "ozempic": DrugPricing(
        generic_name="semaglutide",
        brand_names=["Ozempic", "Wegovy"],
        generic_available=False,
        generic_30_day_cost=None,
        brand_30_day_cost=950.00,
        typical_copay_generic=None,
        typical_copay_brand=150.00,
        common_tier=4,
    ),
    "humira": DrugPricing(
        generic_name="adalimumab",
        brand_names=["Humira"],
        generic_available=True,  # Biosimilars available
        generic_30_day_cost=3500.00,  # Biosimilar
        brand_30_day_cost=6000.00,
        typical_copay_generic=100.00,
        typical_copay_brand=200.00,
        common_tier=5,
    ),
}


# =============================================================================
# Cost Estimation Service
# =============================================================================


class CostEstimationService:
    """
    Estimate medication costs and insurance coverage.

    Features:
    - Drug price lookup
    - Insurance tier estimation
    - Generic alternative suggestions
    - Copay estimation
    """

    def __init__(self):
        self.pricing_db = DRUG_PRICING_DB

        # Build lookup with brand names
        self.name_lookup: dict[str, str] = {}
        for generic, info in self.pricing_db.items():
            self.name_lookup[generic.lower()] = generic
            for brand in info.brand_names:
                self.name_lookup[brand.lower()] = generic

        logger.info("CostEstimationService initialized")

    def get_cost_info(
        self,
        medication: str,
        insurance: InsuranceCoverage | None = None,
    ) -> MedicationCost:
        """
        Get cost information for medication.

        Args:
            medication: Medication name (generic or brand)
            insurance: Patient's insurance information

        Returns:
            MedicationCost with pricing details
        """
        # Lookup medication
        generic_name = self.name_lookup.get(medication.lower())
        pricing = self.pricing_db.get(generic_name) if generic_name else None

        if not pricing:
            return MedicationCost(
                estimated_monthly_cost=None,
                generic_available=False,
                insurance_coverage=CoverageStatus.UNKNOWN,
            )

        # Determine coverage status
        coverage = self._determine_coverage(pricing, insurance)

        # Estimate copay
        copay = self._estimate_copay(pricing, insurance)

        # Determine estimated cost
        if pricing.generic_available and pricing.generic_30_day_cost:
            monthly_cost = pricing.generic_30_day_cost
        elif pricing.brand_30_day_cost:
            monthly_cost = pricing.brand_30_day_cost
        else:
            monthly_cost = None

        prior_auth = self._check_prior_auth(pricing, insurance)

        return MedicationCost(
            estimated_monthly_cost=monthly_cost,
            generic_available=pricing.generic_available,
            generic_cost=pricing.generic_30_day_cost,
            insurance_coverage=coverage,
            copay_estimate=copay,
            prior_auth_notes=prior_auth,
        )

    def _determine_coverage(
        self,
        pricing: DrugPricing,
        insurance: InsuranceCoverage | None,
    ) -> CoverageStatus:
        """Determine insurance coverage status."""
        if not insurance:
            return CoverageStatus.UNKNOWN

        tier = pricing.common_tier

        if insurance.formulary_tier and insurance.formulary_tier < tier:
            return CoverageStatus.NOT_COVERED

        if tier == 1:
            return CoverageStatus.TIER_1
        elif tier == 2:
            return CoverageStatus.TIER_2
        elif tier == 3:
            return CoverageStatus.TIER_3
        elif tier >= 4:
            return CoverageStatus.PRIOR_AUTH_REQUIRED

        return CoverageStatus.COVERED

    def _estimate_copay(
        self,
        pricing: DrugPricing,
        insurance: InsuranceCoverage | None,
    ) -> float | None:
        """Estimate copay based on insurance."""
        if not insurance:
            return None

        # Use insurance copay if available
        if pricing.generic_available and insurance.copay_generic:
            return insurance.copay_generic
        elif insurance.copay_brand:
            return insurance.copay_brand

        # Use typical copays
        if pricing.generic_available and pricing.typical_copay_generic:
            return pricing.typical_copay_generic
        elif pricing.typical_copay_brand:
            return pricing.typical_copay_brand

        return None

    def _check_prior_auth(
        self,
        pricing: DrugPricing,
        insurance: InsuranceCoverage | None,
    ) -> str | None:
        """Check if prior authorization may be required."""
        if not insurance:
            return None

        if insurance.prior_auth_required:
            return "Prior authorization required per patient's plan"

        if pricing.common_tier >= 4:
            return "Prior authorization typically required for this tier"

        return None

    def find_cheaper_alternatives(
        self,
        medication: str,
        max_results: int = 3,
    ) -> list[dict]:
        """
        Find cheaper alternatives in same drug class.

        Args:
            medication: Current medication
            max_results: Maximum alternatives to return

        Returns:
            List of alternative medications with pricing
        """
        # Drug class mappings
        drug_classes = {
            "statins": ["atorvastatin", "rosuvastatin", "simvastatin", "pravastatin"],
            "ace_inhibitors": ["lisinopril", "enalapril", "ramipril"],
            "arbs": ["losartan", "valsartan", "candesartan"],
            "ppis": ["omeprazole", "pantoprazole", "esomeprazole"],
            "ssris": ["sertraline", "fluoxetine", "escitalopram", "citalopram"],
            "metformin": ["metformin"],  # First-line, no alternative needed
        }

        # Find drug class
        med_lower = medication.lower()
        med_class = None

        for class_name, drugs in drug_classes.items():
            if med_lower in drugs:
                med_class = class_name
                break

        if not med_class:
            return []

        # Find cheaper alternatives
        alternatives = []
        current_pricing = self.pricing_db.get(self.name_lookup.get(med_lower))
        current_cost = (
            (
                current_pricing.generic_30_day_cost
                or current_pricing.brand_30_day_cost
                or float("inf")
            )
            if current_pricing
            else float("inf")
        )

        for drug in drug_classes[med_class]:
            if drug.lower() == med_lower:
                continue

            pricing = self.pricing_db.get(drug)
            if pricing:
                cost = pricing.generic_30_day_cost or pricing.brand_30_day_cost
                if cost and cost < current_cost:
                    alternatives.append(
                        {
                            "medication": pricing.generic_name,
                            "brand_names": pricing.brand_names,
                            "monthly_cost": cost,
                            "savings": current_cost - cost,
                            "generic_available": pricing.generic_available,
                        }
                    )

        # Sort by cost
        alternatives.sort(key=lambda x: x["monthly_cost"])

        return alternatives[:max_results]

    def estimate_total_monthly_cost(
        self,
        medications: list[str],
        insurance: InsuranceCoverage | None = None,
    ) -> dict:
        """
        Estimate total monthly medication cost.

        Args:
            medications: List of medication names
            insurance: Patient's insurance

        Returns:
            Cost summary
        """
        total_retail = 0.0
        total_with_insurance = 0.0
        medication_costs = []

        for med in medications:
            cost_info = self.get_cost_info(med, insurance)

            retail = cost_info.estimated_monthly_cost or 0
            with_insurance = cost_info.copay_estimate or retail

            total_retail += retail
            total_with_insurance += with_insurance

            medication_costs.append(
                {
                    "medication": med,
                    "retail_cost": retail,
                    "estimated_copay": cost_info.copay_estimate,
                    "generic_available": cost_info.generic_available,
                }
            )

        return {
            "total_retail": total_retail,
            "total_with_insurance": total_with_insurance,
            "estimated_savings": total_retail - total_with_insurance,
            "medications": medication_costs,
        }


# =============================================================================
# Factory
# =============================================================================


def get_cost_estimation_service() -> CostEstimationService:
    """Get cost estimation service singleton."""
    return CostEstimationService()
