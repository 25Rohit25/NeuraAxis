from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class RuleCategory(str, Enum):
    CRITICAL_LAB = "Critical Lab"
    DRUG_ALLERGY = "Drug Allergy"
    DRUG_INTERACTION = "Drug Interaction"
    DUPLICATE_THERAPY = "Duplicate Therapy"
    DOSE_RANGE = "Dose Range"
    CONTRAINDICATION = "Contraindication"
    PREVENTIVE_CARE = "Preventive Care"
    BEST_PRACTICE = "Best Practice"
    QUALITY_METRIC = "Quality Metric"


class PriorityLevel(int, Enum):
    CRITICAL = 1
    HIGH = 2
    MODERATE = 3
    LOW = 4
    INFO = 5


class LogicOperator(str, Enum):
    EQUALS = "=="
    NOT_EQUALS = "!="
    GREATER_THAN = ">"
    LESS_THAN = "<"
    GREATER_EQUAL = ">="
    LESS_EQUAL = "<="
    IN = "in"
    NOT_IN = "not_in"
    CONTAINS = "contains"
    EXISTS = "exists"


class RuleCondition(BaseModel):
    field: str  # dot notation e.g. "patient.age", "medication.code"
    operator: LogicOperator
    value: Any


class RuleActionType(str, Enum):
    ALERT = "ALERT"
    BLOCK = "BLOCK"
    SUGGEST = "SUGGEST"


class RuleAction(BaseModel):
    type: RuleActionType
    message: str
    suggestion: Optional[str] = None


class CDSSRule(BaseModel):
    id: str
    name: str
    category: RuleCategory
    priority: PriorityLevel
    conditions: List[RuleCondition]  # Implicit AND
    actions: List[RuleAction]
    evidence_link: Optional[str] = None
    enabled: bool = True


class EvaluationRequest(BaseModel):
    patient_data: Dict[str, Any]  # Demographics, Vitals
    medications: List[Dict[str, Any]] = Field(default_factory=list)
    conditions: List[Dict[str, Any]] = Field(default_factory=list)  # Patient Diagnoses
    lab_results: List[Dict[str, Any]] = Field(default_factory=list)
    context_event: str = "general_check"  # Trigger


class Alert(BaseModel):
    rule_id: str
    rule_name: str
    category: RuleCategory
    priority: PriorityLevel
    message: str
    suggestion: Optional[str]
    evidence_link: Optional[str]
    timestamp: str


class EvaluationResponse(BaseModel):
    alerts: List[Alert]
    valid: bool = True
