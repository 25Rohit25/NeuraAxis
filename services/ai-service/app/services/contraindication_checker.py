"""
NEURAXIS - Contraindication Checker
Drug-allergy, drug-drug, and drug-condition interaction checking
"""

import logging
from dataclasses import dataclass

from app.agents.treatment_schemas import (
    Allergy,
    ContraindicationWarning,
    CurrentMedication,
    DrugInteraction,
    InteractionSeverity,
    MedicalCondition,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Drug Allergy Cross-Reactivity Database
# =============================================================================

# Drug classes and their related allergens
DRUG_CLASS_ALLERGENS = {
    "penicillins": {
        "drugs": [
            "amoxicillin",
            "ampicillin",
            "penicillin",
            "piperacillin",
            "nafcillin",
            "oxacillin",
        ],
        "cross_reactive": ["cephalosporins"],  # ~2% cross-reactivity
        "cross_reactive_risk": 0.02,
    },
    "cephalosporins": {
        "drugs": [
            "cephalexin",
            "cefazolin",
            "ceftriaxone",
            "cefepime",
            "cefuroxime",
            "cefpodoxime",
        ],
        "cross_reactive": ["penicillins"],
        "cross_reactive_risk": 0.02,
    },
    "sulfonamides": {
        "drugs": ["sulfamethoxazole", "sulfasalazine", "trimethoprim-sulfamethoxazole", "bactrim"],
        "cross_reactive": [],
    },
    "fluoroquinolones": {
        "drugs": ["ciprofloxacin", "levofloxacin", "moxifloxacin", "ofloxacin"],
        "cross_reactive": [],
    },
    "nsaids": {
        "drugs": [
            "ibuprofen",
            "naproxen",
            "aspirin",
            "ketorolac",
            "indomethacin",
            "meloxicam",
            "celecoxib",
        ],
        "cross_reactive": ["aspirin"],
        "cross_reactive_risk": 0.15,
    },
    "opioids": {
        "drugs": [
            "morphine",
            "codeine",
            "hydrocodone",
            "oxycodone",
            "fentanyl",
            "tramadol",
            "hydromorphone",
        ],
        "cross_reactive": [],
    },
    "ace_inhibitors": {
        "drugs": ["lisinopril", "enalapril", "ramipril", "benazepril", "captopril"],
        "cross_reactive": [],  # ARBs are safe in ACE-I angioedema
    },
    "statins": {
        "drugs": ["atorvastatin", "simvastatin", "rosuvastatin", "pravastatin", "lovastatin"],
        "cross_reactive": [],
    },
}


# =============================================================================
# Drug-Condition Contraindications
# =============================================================================

CONTRAINDICATIONS = {
    "metformin": {
        "conditions": [
            {
                "condition": "chronic kidney disease",
                "icd10_prefix": "N18",
                "severity": "relative",
                "note": "Avoid if eGFR < 30, use caution 30-45",
            },
            {"condition": "liver failure", "icd10_prefix": "K72", "severity": "absolute"},
            {"condition": "metabolic acidosis", "icd10_prefix": "E87.2", "severity": "absolute"},
        ],
    },
    "lisinopril": {
        "conditions": [
            {"condition": "pregnancy", "icd10_prefix": "Z33", "severity": "absolute"},
            {
                "condition": "bilateral renal artery stenosis",
                "icd10_prefix": "I70.1",
                "severity": "absolute",
            },
            {"condition": "angioedema history", "icd10_prefix": "T78.3", "severity": "absolute"},
            {"condition": "hyperkalemia", "icd10_prefix": "E87.5", "severity": "relative"},
        ],
    },
    "warfarin": {
        "conditions": [
            {"condition": "active bleeding", "icd10_prefix": "K92.2", "severity": "absolute"},
            {"condition": "thrombocytopenia", "icd10_prefix": "D69.6", "severity": "relative"},
            {"condition": "pregnancy", "icd10_prefix": "Z33", "severity": "absolute"},
        ],
    },
    "aspirin": {
        "conditions": [
            {"condition": "peptic ulcer", "icd10_prefix": "K27", "severity": "relative"},
            {"condition": "bleeding disorder", "icd10_prefix": "D68", "severity": "relative"},
            {
                "condition": "asthma (aspirin-sensitive)",
                "icd10_prefix": "J45",
                "severity": "relative",
            },
        ],
    },
    "atorvastatin": {
        "conditions": [
            {"condition": "active liver disease", "icd10_prefix": "K75", "severity": "absolute"},
            {"condition": "pregnancy", "icd10_prefix": "Z33", "severity": "absolute"},
        ],
    },
    "nsaids": {
        "conditions": [
            {"condition": "chronic kidney disease", "icd10_prefix": "N18", "severity": "relative"},
            {"condition": "heart failure", "icd10_prefix": "I50", "severity": "relative"},
            {"condition": "peptic ulcer", "icd10_prefix": "K27", "severity": "relative"},
            {"condition": "gi bleeding", "icd10_prefix": "K92", "severity": "absolute"},
        ],
    },
}


# =============================================================================
# Drug-Drug Interactions
# =============================================================================

DRUG_INTERACTIONS = [
    {
        "drug1": "warfarin",
        "drug2_list": ["aspirin", "ibuprofen", "naproxen"],
        "severity": InteractionSeverity.SEVERE,
        "description": "Increased bleeding risk",
        "effect": "NSAIDs inhibit platelet function and may increase warfarin levels",
        "management": "Avoid combination if possible. If necessary, use with extreme caution and monitor closely",
    },
    {
        "drug1": "warfarin",
        "drug2_list": ["amiodarone"],
        "severity": InteractionSeverity.SEVERE,
        "description": "Increased warfarin effect",
        "effect": "Amiodarone inhibits warfarin metabolism via CYP2C9",
        "management": "Reduce warfarin dose by 30-50%. Monitor INR closely",
    },
    {
        "drug1": "lisinopril",
        "drug2_list": ["spironolactone", "triamterene", "potassium supplements"],
        "severity": InteractionSeverity.MODERATE,
        "description": "Hyperkalemia risk",
        "effect": "Both drugs increase potassium retention",
        "management": "Monitor potassium levels regularly. Use with caution",
    },
    {
        "drug1": "lisinopril",
        "drug2_list": ["ibuprofen", "naproxen", "meloxicam"],
        "severity": InteractionSeverity.MODERATE,
        "description": "Reduced antihypertensive effect and renal risk",
        "effect": "NSAIDs may reduce ACE inhibitor efficacy and increase renal injury risk",
        "management": "Use alternative pain medication. Monitor blood pressure and renal function",
    },
    {
        "drug1": "metformin",
        "drug2_list": ["contrast media"],
        "severity": InteractionSeverity.SEVERE,
        "description": "Lactic acidosis risk",
        "effect": "Iodinated contrast may cause acute kidney injury, increasing metformin accumulation",
        "management": "Hold metformin before and 48h after contrast. Check renal function before resuming",
    },
    {
        "drug1": "simvastatin",
        "drug2_list": ["amiodarone", "diltiazem", "verapamil"],
        "severity": InteractionSeverity.SEVERE,
        "description": "Increased rhabdomyolysis risk",
        "effect": "CYP3A4 inhibition increases statin levels",
        "management": "Limit simvastatin to 10-20mg. Consider alternative statin",
    },
    {
        "drug1": "fluoxetine",
        "drug2_list": ["tramadol", "meperidine", "fentanyl"],
        "severity": InteractionSeverity.SEVERE,
        "description": "Serotonin syndrome risk",
        "effect": "Combined serotonergic activity may cause serotonin syndrome",
        "management": "Avoid combination. If necessary, monitor closely for symptoms",
    },
    {
        "drug1": "digoxin",
        "drug2_list": ["amiodarone", "verapamil", "quinidine"],
        "severity": InteractionSeverity.SEVERE,
        "description": "Digoxin toxicity risk",
        "effect": "These drugs increase digoxin levels",
        "management": "Reduce digoxin dose by 50%. Monitor digoxin levels",
    },
    {
        "drug1": "methotrexate",
        "drug2_list": ["trimethoprim", "sulfamethoxazole"],
        "severity": InteractionSeverity.CONTRAINDICATED,
        "description": "Severe bone marrow suppression",
        "effect": "Both drugs inhibit folate metabolism",
        "management": "AVOID combination. Use alternative antibiotics",
    },
    {
        "drug1": "clopidogrel",
        "drug2_list": ["omeprazole", "esomeprazole"],
        "severity": InteractionSeverity.MODERATE,
        "description": "Reduced antiplatelet effect",
        "effect": "PPI inhibits CYP2C19, reducing clopidogrel activation",
        "management": "Use pantoprazole instead (less CYP2C19 inhibition)",
    },
]


# =============================================================================
# Contraindication Checker
# =============================================================================


class ContraindicationChecker:
    """
    Check medications for contraindications.

    Features:
    - Allergy checking with cross-reactivity
    - Drug-condition contraindications
    - Drug-drug interactions
    """

    def __init__(self):
        self.drug_classes = DRUG_CLASS_ALLERGENS
        self.contraindications = CONTRAINDICATIONS
        self.interactions = DRUG_INTERACTIONS

        # Build reverse lookup for drug classes
        self.drug_to_class: dict[str, str] = {}
        for class_name, info in self.drug_classes.items():
            for drug in info["drugs"]:
                self.drug_to_class[drug.lower()] = class_name

        logger.info("ContraindicationChecker initialized")

    def check_allergies(
        self,
        medication: str,
        allergies: list[Allergy],
    ) -> list[ContraindicationWarning]:
        """
        Check medication against patient allergies.

        Args:
            medication: Medication to check
            allergies: Patient's allergies

        Returns:
            List of warnings
        """
        warnings = []
        med_lower = medication.lower()

        for allergy in allergies:
            allergen = allergy.allergen.lower()

            # Direct match
            if allergen in med_lower or med_lower in allergen:
                warnings.append(
                    ContraindicationWarning(
                        medication=medication,
                        reason=f"Patient has documented allergy to {allergy.allergen}",
                        condition_or_allergy=f"{allergy.allergen} (reaction: {allergy.reaction or 'unknown'})",
                        severity="absolute",
                        alternative_suggested=self._get_alternative_for_allergy(
                            medication, allergen
                        ),
                    )
                )
                continue

            # Check drug class
            med_class = self.drug_to_class.get(med_lower)
            allergen_class = self.drug_to_class.get(allergen)

            if med_class and med_class == allergen_class:
                warnings.append(
                    ContraindicationWarning(
                        medication=medication,
                        reason=f"Same drug class ({med_class}) as allergen",
                        condition_or_allergy=allergy.allergen,
                        severity="absolute",
                        alternative_suggested=self._get_alternative_for_allergy(
                            medication, allergen
                        ),
                    )
                )

            # Check cross-reactivity
            if allergen_class:
                class_info = self.drug_classes.get(allergen_class, {})
                cross_reactive = class_info.get("cross_reactive", [])

                if med_class and med_class in cross_reactive:
                    risk = class_info.get("cross_reactive_risk", 0.1)
                    warnings.append(
                        ContraindicationWarning(
                            medication=medication,
                            reason=f"Cross-reactivity risk (~{int(risk * 100)}%) with {allergen_class}",
                            condition_or_allergy=allergy.allergen,
                            severity="relative",
                            alternative_suggested=f"Consider skin testing or use non-{med_class} alternative",
                        )
                    )

        return warnings

    def check_conditions(
        self,
        medication: str,
        conditions: list[MedicalCondition],
    ) -> list[ContraindicationWarning]:
        """
        Check medication against patient conditions.

        Args:
            medication: Medication to check
            conditions: Patient's medical conditions

        Returns:
            List of contraindication warnings
        """
        warnings = []
        med_lower = medication.lower()

        # Get contraindications for this medication
        med_contraindications = self.contraindications.get(med_lower, {}).get("conditions", [])

        # Also check if it's an NSAID
        if med_lower in self.drug_classes.get("nsaids", {}).get("drugs", []):
            med_contraindications.extend(
                self.contraindications.get("nsaids", {}).get("conditions", [])
            )

        for condition in conditions:
            for ci in med_contraindications:
                # Check ICD-10 prefix match
                if condition.icd10_code and ci.get("icd10_prefix"):
                    if condition.icd10_code.upper().startswith(ci["icd10_prefix"]):
                        warnings.append(
                            ContraindicationWarning(
                                medication=medication,
                                reason=ci.get("note", f"Contraindicated with {ci['condition']}"),
                                condition_or_allergy=f"{condition.name} ({condition.icd10_code})",
                                severity=ci["severity"],
                            )
                        )
                        continue

                # Check condition name match
                if ci["condition"].lower() in condition.name.lower():
                    warnings.append(
                        ContraindicationWarning(
                            medication=medication,
                            reason=ci.get("note", f"Contraindicated with {condition.name}"),
                            condition_or_allergy=condition.name,
                            severity=ci["severity"],
                        )
                    )

        return warnings

    def check_interactions(
        self,
        medication: str,
        current_medications: list[CurrentMedication],
    ) -> list[DrugInteraction]:
        """
        Check for drug-drug interactions.

        Args:
            medication: New medication to check
            current_medications: Patient's current medications

        Returns:
            List of drug interactions
        """
        interactions = []
        med_lower = medication.lower()

        current_med_names = [m.name.lower() for m in current_medications]

        for interaction in self.interactions:
            drug1 = interaction["drug1"].lower()
            drug2_list = [d.lower() for d in interaction["drug2_list"]]

            # Check if new medication is drug1 and patient takes drug2
            if med_lower == drug1 or med_lower in drug2_list:
                for current_med in current_med_names:
                    # Check direct match
                    target_drugs = drug2_list if med_lower == drug1 else [drug1]

                    for target in target_drugs:
                        if target in current_med or current_med in target:
                            interactions.append(
                                DrugInteraction(
                                    medication_1=medication,
                                    medication_2=current_med,
                                    severity=interaction["severity"],
                                    description=interaction["description"],
                                    clinical_effect=interaction["effect"],
                                    management=interaction["management"],
                                )
                            )

        return interactions

    def check_all(
        self,
        medication: str,
        allergies: list[Allergy],
        conditions: list[MedicalCondition],
        current_medications: list[CurrentMedication],
    ) -> tuple[list[ContraindicationWarning], list[DrugInteraction]]:
        """
        Perform all safety checks.

        Args:
            medication: Medication to check
            allergies: Patient allergies
            conditions: Medical conditions
            current_medications: Current medications

        Returns:
            Tuple of (contraindication warnings, drug interactions)
        """
        warnings = []

        # Allergy check
        warnings.extend(self.check_allergies(medication, allergies))

        # Condition check
        warnings.extend(self.check_conditions(medication, conditions))

        # Interaction check
        interactions = self.check_interactions(medication, current_medications)

        return warnings, interactions

    def _get_alternative_for_allergy(
        self,
        medication: str,
        allergen: str,
    ) -> str | None:
        """Suggest alternative medication for allergy."""
        med_class = self.drug_to_class.get(medication.lower())

        alternatives = {
            "penicillins": "Consider azithromycin, fluoroquinolone, or doxycycline",
            "cephalosporins": "Consider azithromycin or fluoroquinolone",
            "sulfonamides": "Use non-sulfa antibiotics",
            "nsaids": "Consider acetaminophen for pain relief",
            "ace_inhibitors": "Consider ARB (angiotensin receptor blocker)",
            "statins": "Try different statin or consider ezetimibe",
        }

        return alternatives.get(med_class)

    def is_safe(
        self,
        medication: str,
        allergies: list[Allergy],
        conditions: list[MedicalCondition],
        current_medications: list[CurrentMedication],
    ) -> bool:
        """
        Quick check if medication is safe.

        Returns:
            True if no absolute contraindications
        """
        warnings, interactions = self.check_all(
            medication, allergies, conditions, current_medications
        )

        # Check for absolute contraindications
        for w in warnings:
            if w.severity == "absolute":
                return False

        # Check for contraindicated interactions
        for i in interactions:
            if i.severity == InteractionSeverity.CONTRAINDICATED:
                return False

        return True


# =============================================================================
# Factory
# =============================================================================


def get_contraindication_checker() -> ContraindicationChecker:
    """Get contraindication checker singleton."""
    return ContraindicationChecker()
