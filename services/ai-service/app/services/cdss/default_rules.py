from typing import List

from app.services.cdss.schemas import (
    CDSSRule,
    LogicOperator,
    PriorityLevel,
    RuleAction,
    RuleActionType,
    RuleCategory,
    RuleCondition,
)


def get_default_rules() -> List[CDSSRule]:
    return [
        CDSSRule(
            id="rule-critical-hba1c",
            name="Critical HbA1c Level",
            category=RuleCategory.CRITICAL_LAB,
            priority=PriorityLevel.CRITICAL,
            conditions=[
                RuleCondition(field="labs.HbA1c", operator=LogicOperator.GREATER_THAN, value=9.0)
            ],
            actions=[
                RuleAction(
                    type=RuleActionType.ALERT,
                    message="Patient has critical HbA1c level (>9.0). Immediate endocrine consult recommended.",
                    suggestion="Order endocrine consult.",
                )
            ],
            evidence_link="https://diabetes.org/guidelines",
        ),
        CDSSRule(
            id="rule-ace-hf",
            name="ACE Inhibitor in Heart Failure",
            category=RuleCategory.BEST_PRACTICE,
            priority=PriorityLevel.MODERATE,
            conditions=[
                RuleCondition(
                    field="conditions_names", operator=LogicOperator.CONTAINS, value="heart failure"
                ),
                RuleCondition(
                    field="medications",
                    operator=LogicOperator.NOT_IN,  # Simplified check (should check class)
                    value=["lisinopril", "enalapril", "captopril"],
                ),
            ],
            actions=[
                RuleAction(
                    type=RuleActionType.SUGGEST,
                    message="Patient with Heart Failure should typically be on an ACE Inhibitor.",
                    suggestion="Consider prescribing Lisinopril.",
                )
            ],
            evidence_link="https://heart.org/guidelines/hf",
        ),
        CDSSRule(
            id="rule-beta-asthma",
            name="Beta Blocker in Asthma",
            category=RuleCategory.CONTRAINDICATION,
            priority=PriorityLevel.HIGH,  # Warning
            conditions=[
                RuleCondition(
                    field="conditions_names", operator=LogicOperator.CONTAINS, value="asthma"
                ),
                RuleCondition(
                    field="medications", operator=LogicOperator.CONTAINS, value="propranolol"
                ),
            ],
            actions=[
                RuleAction(
                    type=RuleActionType.ALERT,
                    message="Non-selective Beta Blockers (Propranolol) may exacerbate Asthma.",
                    suggestion="Consider cardioselective beta blocker or alternative.",
                )
            ],
        ),
        CDSSRule(
            id="rule-dose-tylenol",
            name="Acetaminophen Max Dose",
            category=RuleCategory.DOSE_RANGE,
            priority=PriorityLevel.CRITICAL,
            conditions=[
                # Simplified check for total dose if pre-calculated
                # Real implementation would sum up doses
                RuleCondition(
                    field="medication_objects.acetaminophen_total_daily_mg",
                    operator=LogicOperator.GREATER_THAN,
                    value=4000,
                )
            ],
            actions=[
                RuleAction(
                    type=RuleActionType.BLOCK,
                    message="Acetaminophen daily dose exceeds 4000mg. Risk of liver toxicity.",
                )
            ],
        ),
        CDSSRule(
            id="rule-statin-cad",
            name="Statin in Coronary Artery Disease",
            category=RuleCategory.BEST_PRACTICE,
            priority=PriorityLevel.HIGH,
            conditions=[
                RuleCondition(
                    field="conditions_names",
                    operator=LogicOperator.CONTAINS,
                    value="coronary artery disease",
                ),
                RuleCondition(
                    field="medications",
                    operator=LogicOperator.NOT_IN,  # Check generic names
                    value=["atorvastatin", "rosuvastatin", "simvastatin"],
                ),
            ],
            actions=[
                RuleAction(
                    type=RuleActionType.SUGGEST,
                    message="Patient with CAD should be on high-intensity Statin.",
                )
            ],
        ),
    ]
