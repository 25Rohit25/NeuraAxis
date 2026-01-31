import logging
from datetime import datetime
from typing import Any, Dict, List, Union

from app.services.cdss.schemas import (
    Alert,
    CDSSRule,
    EvaluationRequest,
    EvaluationResponse,
    LogicOperator,
    RuleCondition,
)

logger = logging.getLogger(__name__)


class RulesEngine:
    def __init__(self):
        self.rules: List[CDSSRule] = []

    def load_rules(self, rules: List[CDSSRule]):
        self.rules = rules

    def evaluate(self, request: EvaluationRequest) -> EvaluationResponse:
        alerts: List[Alert] = []

        # Helper to traverse data
        # We flatten the request into a queryable context
        context = self._build_context(request)

        for rule in self.rules:
            if not rule.enabled:
                continue

            if self._check_conditions(rule.conditions, context):
                # All conditions met (AND logic)
                for action in rule.actions:
                    alerts.append(
                        Alert(
                            rule_id=rule.id,
                            rule_name=rule.name,
                            category=rule.category,
                            priority=rule.priority,
                            message=action.message,
                            suggestion=action.suggestion,
                            evidence_link=rule.evidence_link,
                            timestamp=datetime.now().isoformat(),
                        )
                    )

        return EvaluationResponse(
            alerts=sorted(alerts, key=lambda x: x.priority),
            valid=not any(a.priority == 1 for a in alerts),  # Block if critical
        )

    def _build_context(self, request: EvaluationRequest) -> Dict[str, Any]:
        """Flatten data for easier rule triggers."""
        ctx = {
            "patient": request.patient_data,
            "medications": [m.get("name", "").lower() for m in request.medications],
            "medication_objects": request.medications,
            "conditions": [c.get("code", "") for c in request.conditions],
            "conditions_names": [c.get("name", "").lower() for c in request.conditions],
            "labs": {
                l.get("code"): l.get("value") for l in request.lab_results
            },  # Map code -> value
        }
        # Special handling for "last_hba1c" etc could be added here
        return ctx

    def _check_conditions(self, conditions: List[RuleCondition], context: Dict[str, Any]) -> bool:
        for condition in conditions:
            if not self._evaluate_condition(condition, context):
                return False
        return True

    def _evaluate_condition(self, condition: RuleCondition, context: Dict[str, Any]) -> bool:
        # Resolve value from context
        actual_value = self._get_value(condition.field, context)

        if actual_value is None:
            return False

        op = condition.operator
        target = condition.value

        try:
            if op == LogicOperator.EQUALS:
                return actual_value == target
            elif op == LogicOperator.NOT_EQUALS:
                return actual_value != target
            elif op == LogicOperator.GREATER_THAN:
                return float(actual_value) > float(target)
            elif op == LogicOperator.LESS_THAN:
                return float(actual_value) < float(target)
            elif op == LogicOperator.GREATER_EQUAL:
                return float(actual_value) >= float(target)
            elif op == LogicOperator.LESS_EQUAL:
                return float(actual_value) <= float(target)
            elif op == LogicOperator.IN:
                return actual_value in target  # target should be list
            elif op == LogicOperator.NOT_IN:
                return actual_value not in target
            elif op == LogicOperator.CONTAINS:
                # e.g. list of meds contains 'aspirin'
                if isinstance(actual_value, list):
                    return target in actual_value
                return str(target) in str(actual_value)
            elif op == LogicOperator.EXISTS:
                return (actual_value is not None) == target
        except Exception:
            return False

        return False

    def _get_value(self, field: str, context: Dict[str, Any]) -> Any:
        """
        Supports:
        - patient.age
        - labs.HbA1c
        - medications (returns list)
        """
        parts = field.split(".")
        current = context

        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            else:
                return None

            if current is None:
                return None

        return current


# Singleton
engine = RulesEngine()


def get_rules_engine() -> RulesEngine:
    return engine
