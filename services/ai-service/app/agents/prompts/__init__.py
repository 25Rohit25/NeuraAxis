"""
NEURAXIS - Prompts Package
Prompt templates for AI agents
"""

from app.agents.prompts.diagnostic_template import (
    DIAGNOSTIC_SYSTEM_PROMPT,
    FEW_SHOT_EXAMPLES,
    format_history,
    format_labs,
    format_medications,
    format_symptoms,
    format_vitals,
    get_diagnostic_prompt_template,
)

__all__ = [
    "get_diagnostic_prompt_template",
    "format_symptoms",
    "format_vitals",
    "format_labs",
    "format_history",
    "format_medications",
    "DIAGNOSTIC_SYSTEM_PROMPT",
    "FEW_SHOT_EXAMPLES",
]
