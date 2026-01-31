"""
NEURAXIS - Dosage Calculation Utilities
Weight-based, age-based, and organ function dosing
"""

import logging
from dataclasses import dataclass
from typing import Any

from app.agents.treatment_schemas import (
    DosageCalculation,
    HepaticFunction,
    PatientDemographics,
    RenalFunction,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Dosage Adjustment Factors
# =============================================================================


@dataclass
class DosageRange:
    """Safe dosage range for a medication."""

    min_dose: float
    max_dose: float
    unit: str
    frequency: str
    route: str = "oral"


@dataclass
class RenalDoseAdjustment:
    """Renal dose adjustment rules."""

    egfr_threshold: float  # Below this eGFR, adjust dose
    adjustment_factor: float  # Multiply dose by this
    max_dose: float | None = None
    avoid_if_egfr_below: float | None = None  # Contraindicated below this


@dataclass
class HepaticDoseAdjustment:
    """Hepatic dose adjustment rules."""

    child_pugh_class: str  # A, B, or C
    adjustment_factor: float
    max_dose: float | None = None
    avoid: bool = False


@dataclass
class AgeDoseAdjustment:
    """Age-based dose adjustment."""

    min_age: int
    max_age: int
    adjustment_factor: float
    max_dose: float | None = None
    special_consideration: str | None = None


# =============================================================================
# Medication Dosing Database
# =============================================================================

# Common medications with their dosing parameters
MEDICATION_DOSING = {
    "metformin": {
        "weight_based": False,
        "adult_dose": DosageRange(500, 2550, "mg", "daily", "oral"),
        "starting_dose": "500 mg twice daily",
        "titration": "Increase by 500 mg weekly as tolerated",
        "renal_adjustment": [
            RenalDoseAdjustment(45, 1.0),  # Normal above eGFR 45
            RenalDoseAdjustment(30, 0.5, max_dose=1000),  # Reduce if eGFR 30-45
            RenalDoseAdjustment(0, 0, avoid_if_egfr_below=30),  # Avoid if eGFR < 30
        ],
        "hepatic_adjustment": [
            HepaticDoseAdjustment("C", 0, avoid=True),  # Avoid in severe liver disease
        ],
    },
    "lisinopril": {
        "weight_based": False,
        "adult_dose": DosageRange(2.5, 40, "mg", "once daily", "oral"),
        "starting_dose": "5-10 mg once daily",
        "renal_adjustment": [
            RenalDoseAdjustment(30, 0.5),  # Start at 2.5-5 mg if eGFR < 30
        ],
    },
    "atorvastatin": {
        "weight_based": False,
        "adult_dose": DosageRange(10, 80, "mg", "once daily", "oral"),
        "starting_dose": "10-20 mg once daily",
        "hepatic_adjustment": [
            HepaticDoseAdjustment("B", 0.5),
            HepaticDoseAdjustment("C", 0, avoid=True),
        ],
    },
    "amoxicillin": {
        "weight_based": True,
        "adult_dose": DosageRange(250, 3000, "mg", "daily", "oral"),
        "pediatric_dose_per_kg": 25,  # mg/kg/day
        "max_pediatric_dose": 3000,  # mg/day
        "renal_adjustment": [
            RenalDoseAdjustment(30, 0.67),  # Reduce frequency to q12h
            RenalDoseAdjustment(10, 0.5),  # Reduce dose by 50%
        ],
    },
    "vancomycin": {
        "weight_based": True,
        "adult_dose_per_kg": 15,  # mg/kg
        "frequency": "every 12 hours",
        "renal_adjustment": [
            RenalDoseAdjustment(50, 1.0),
            RenalDoseAdjustment(30, 0.75),
            RenalDoseAdjustment(10, 0.5),
        ],
        "requires_therapeutic_monitoring": True,
    },
    "warfarin": {
        "weight_based": False,
        "adult_dose": DosageRange(1, 10, "mg", "once daily", "oral"),
        "starting_dose": "5 mg once daily (adjust based on INR)",
        "hepatic_adjustment": [
            HepaticDoseAdjustment("B", 0.5),
            HepaticDoseAdjustment("C", 0.25),
        ],
        "age_adjustment": [
            AgeDoseAdjustment(65, 150, 0.75, special_consideration="Elderly more sensitive"),
        ],
    },
    "gabapentin": {
        "weight_based": False,
        "adult_dose": DosageRange(100, 3600, "mg", "daily", "oral"),
        "starting_dose": "300 mg once daily at bedtime",
        "titration": "May increase by 300 mg every 3 days",
        "renal_adjustment": [
            RenalDoseAdjustment(60, 1.0, max_dose=3600),
            RenalDoseAdjustment(30, 0.5, max_dose=1400),
            RenalDoseAdjustment(15, 0.25, max_dose=700),
        ],
    },
    "acetaminophen": {
        "weight_based": True,
        "adult_dose": DosageRange(325, 4000, "mg", "daily", "oral"),
        "adult_single_dose": "650-1000 mg every 4-6 hours",
        "pediatric_dose_per_kg": 15,  # mg/kg per dose
        "max_pediatric_single_dose": 1000,
        "hepatic_adjustment": [
            HepaticDoseAdjustment("B", 0.5, max_dose=2000),
            HepaticDoseAdjustment("C", 0.25, max_dose=1000),
        ],
    },
}


# =============================================================================
# Dosage Calculator
# =============================================================================


class DosageCalculator:
    """
    Calculate medication dosages based on patient factors.

    Features:
    - Weight-based dosing
    - Age-based adjustments
    - Renal function adjustments
    - Hepatic function adjustments
    - BSA-based dosing (for chemotherapy)
    """

    def __init__(self):
        self.medication_db = MEDICATION_DOSING
        logger.info("DosageCalculator initialized")

    def calculate_dose(
        self,
        medication_name: str,
        patient: PatientDemographics,
        renal_function: RenalFunction | None = None,
        hepatic_function: HepaticFunction | None = None,
        indication: str | None = None,
    ) -> DosageCalculation:
        """
        Calculate appropriate dose for patient.

        Args:
            medication_name: Name of medication
            patient: Patient demographics
            renal_function: Renal function labs
            hepatic_function: Hepatic function labs
            indication: Clinical indication

        Returns:
            DosageCalculation with details
        """
        med_name = medication_name.lower().strip()
        adjustments = []

        # Get medication info
        med_info = self.medication_db.get(med_name, {})

        if not med_info:
            # Default for unknown medications
            return DosageCalculation(
                calculated_dose="See prescribing information",
                calculation_method="manual",
                formula_used=None,
                adjustments=["Medication not in dosing database - use clinical judgment"],
            )

        # Determine base dose
        if med_info.get("weight_based") and patient.weight_kg:
            # Weight-based calculation
            dose_per_kg = med_info.get("adult_dose_per_kg") or med_info.get(
                "pediatric_dose_per_kg", 0
            )
            base_dose = patient.weight_kg * dose_per_kg
            calculation_method = "weight-based"
            formula = f"{dose_per_kg} mg/kg × {patient.weight_kg} kg"
        else:
            # Fixed dose
            dose_range = med_info.get("adult_dose")
            if dose_range:
                base_dose = dose_range.min_dose
                formula = med_info.get("starting_dose", f"{base_dose} {dose_range.unit}")
            else:
                base_dose = 0
                formula = "See prescribing information"
            calculation_method = "fixed"

        final_dose = base_dose

        # Apply renal adjustments
        if renal_function and renal_function.egfr:
            renal_adj = self._get_renal_adjustment(med_name, renal_function.egfr)
            if renal_adj:
                if (
                    renal_adj.avoid_if_egfr_below
                    and renal_function.egfr < renal_adj.avoid_if_egfr_below
                ):
                    adjustments.append(
                        f"CONTRAINDICATED: Avoid if eGFR < {renal_adj.avoid_if_egfr_below}"
                    )
                elif renal_adj.adjustment_factor < 1:
                    final_dose *= renal_adj.adjustment_factor
                    adjustments.append(
                        f"Renal adjustment: {int(renal_adj.adjustment_factor * 100)}% of dose "
                        f"(eGFR {renal_function.egfr})"
                    )
                    if renal_adj.max_dose:
                        final_dose = min(final_dose, renal_adj.max_dose)
                        adjustments.append(f"Max dose: {renal_adj.max_dose} mg")

        # Apply hepatic adjustments
        if hepatic_function:
            child_pugh = hepatic_function.child_pugh_score
            if child_pugh:
                hepatic_adj = self._get_hepatic_adjustment(med_name, child_pugh)
                if hepatic_adj:
                    if hepatic_adj.avoid:
                        adjustments.append(
                            f"CONTRAINDICATED: Avoid in Child-Pugh class {child_pugh}"
                        )
                    elif hepatic_adj.adjustment_factor < 1:
                        final_dose *= hepatic_adj.adjustment_factor
                        adjustments.append(
                            f"Hepatic adjustment: {int(hepatic_adj.adjustment_factor * 100)}% "
                            f"(Child-Pugh {child_pugh})"
                        )

        # Apply age adjustments
        age_adj = self._get_age_adjustment(med_name, patient.age)
        if age_adj:
            final_dose *= age_adj.adjustment_factor
            adjustments.append(
                f"Age adjustment: {age_adj.special_consideration or 'Elderly dosing'}"
            )
            if age_adj.max_dose:
                final_dose = min(final_dose, age_adj.max_dose)

        # Pediatric adjustments
        if patient.age < 18:
            ped_max = med_info.get("max_pediatric_dose")
            if ped_max:
                final_dose = min(final_dose, ped_max)
                adjustments.append(f"Pediatric max dose: {ped_max} mg")

        # Format final dose
        dose_range = med_info.get("adult_dose")
        unit = dose_range.unit if dose_range else "mg"

        # Round to common increments
        final_dose = self._round_dose(final_dose, unit)

        return DosageCalculation(
            calculated_dose=f"{final_dose} {unit}",
            calculation_method=calculation_method,
            formula_used=formula,
            adjustments=adjustments,
        )

    def _get_renal_adjustment(
        self,
        medication: str,
        egfr: float,
    ) -> RenalDoseAdjustment | None:
        """Get appropriate renal adjustment."""
        med_info = self.medication_db.get(medication.lower(), {})
        adjustments = med_info.get("renal_adjustment", [])

        # Find applicable adjustment (sorted by threshold descending)
        for adj in sorted(adjustments, key=lambda x: x.egfr_threshold, reverse=True):
            if egfr < adj.egfr_threshold:
                return adj

        return None

    def _get_hepatic_adjustment(
        self,
        medication: str,
        child_pugh: str,
    ) -> HepaticDoseAdjustment | None:
        """Get appropriate hepatic adjustment."""
        med_info = self.medication_db.get(medication.lower(), {})
        adjustments = med_info.get("hepatic_adjustment", [])

        for adj in adjustments:
            if adj.child_pugh_class == child_pugh:
                return adj

        return None

    def _get_age_adjustment(
        self,
        medication: str,
        age: int,
    ) -> AgeDoseAdjustment | None:
        """Get appropriate age adjustment."""
        med_info = self.medication_db.get(medication.lower(), {})
        adjustments = med_info.get("age_adjustment", [])

        for adj in adjustments:
            if adj.min_age <= age <= adj.max_age:
                return adj

        return None

    def _round_dose(self, dose: float, unit: str) -> float:
        """Round dose to practical increments."""
        if dose <= 0:
            return dose

        # Common rounding rules
        if dose < 10:
            return round(dose * 2) / 2  # Round to 0.5
        elif dose < 100:
            return round(dose / 5) * 5  # Round to 5
        elif dose < 500:
            return round(dose / 25) * 25  # Round to 25
        else:
            return round(dose / 100) * 100  # Round to 100

    def calculate_pediatric_dose(
        self,
        medication_name: str,
        weight_kg: float,
        age_years: int,
        dose_per_kg: float | None = None,
    ) -> DosageCalculation:
        """
        Calculate pediatric dose.

        Args:
            medication_name: Medication name
            weight_kg: Patient weight in kg
            age_years: Patient age in years
            dose_per_kg: Override dose per kg if known

        Returns:
            DosageCalculation
        """
        med_info = self.medication_db.get(medication_name.lower(), {})

        if dose_per_kg is None:
            dose_per_kg = med_info.get("pediatric_dose_per_kg", 10)

        calculated = weight_kg * dose_per_kg
        max_dose = med_info.get("max_pediatric_dose", float("inf"))

        final_dose = min(calculated, max_dose)
        final_dose = self._round_dose(final_dose, "mg")

        adjustments = []
        if calculated > max_dose:
            adjustments.append(f"Capped at max pediatric dose: {max_dose} mg")

        return DosageCalculation(
            calculated_dose=f"{final_dose} mg",
            calculation_method="weight-based",
            formula_used=f"{dose_per_kg} mg/kg × {weight_kg} kg = {calculated:.1f} mg",
            adjustments=adjustments,
        )

    def calculate_bsa_dose(
        self,
        dose_per_m2: float,
        height_cm: float,
        weight_kg: float,
        max_dose: float | None = None,
    ) -> DosageCalculation:
        """
        Calculate BSA-based dose (commonly used for chemotherapy).

        Args:
            dose_per_m2: Dose per m² BSA
            height_cm: Patient height
            weight_kg: Patient weight
            max_dose: Maximum allowed dose

        Returns:
            DosageCalculation
        """
        # Mosteller BSA formula
        bsa = ((weight_kg * height_cm) / 3600) ** 0.5
        calculated = dose_per_m2 * bsa

        adjustments = []
        if max_dose and calculated > max_dose:
            calculated = max_dose
            adjustments.append(f"Capped at max dose: {max_dose} mg")

        calculated = self._round_dose(calculated, "mg")

        return DosageCalculation(
            calculated_dose=f"{calculated} mg",
            calculation_method="bsa-based",
            formula_used=f"{dose_per_m2} mg/m² × {bsa:.2f} m² = {calculated:.1f} mg",
            adjustments=adjustments,
        )


# =============================================================================
# eGFR Calculator
# =============================================================================


def calculate_egfr(
    creatinine: float,
    age: int,
    gender: str,
    race: str | None = None,
) -> float:
    """
    Calculate eGFR using CKD-EPI 2021 equation (race-free).

    Args:
        creatinine: Serum creatinine in mg/dL
        age: Patient age in years
        gender: male or female
        race: Not used in 2021 equation

    Returns:
        eGFR in mL/min/1.73m²
    """
    is_female = gender.lower() in ["female", "f"]

    if is_female:
        kappa = 0.7
        alpha = -0.241
        sex_factor = 1.012
    else:
        kappa = 0.9
        alpha = -0.302
        sex_factor = 1.0

    cr_ratio = creatinine / kappa

    if cr_ratio <= 1:
        egfr = 142 * (cr_ratio**alpha) * (0.9938**age) * sex_factor
    else:
        egfr = 142 * (cr_ratio**-1.200) * (0.9938**age) * sex_factor

    return round(egfr, 1)


# =============================================================================
# Factory
# =============================================================================


def get_dosage_calculator() -> DosageCalculator:
    """Get dosage calculator singleton."""
    return DosageCalculator()
