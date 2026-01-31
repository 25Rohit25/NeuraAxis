"""
NEURAXIS - Diagnostic Agent
AI-powered medical diagnostic analysis using GPT-4o
"""

import asyncio
import hashlib
import json
import logging
import time
from datetime import datetime
from typing import Any
from uuid import uuid4

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnableWithFallbacks
from langchain_openai import ChatOpenAI
from openai import APIConnectionError, APIError, RateLimitError
from pydantic import ValidationError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.agents.icd10_validator import get_icd10_validator, validate_diagnosis_codes
from app.agents.prompts.diagnostic_template import (
    format_history,
    format_labs,
    format_medications,
    format_symptoms,
    format_vitals,
    get_diagnostic_prompt_template,
)
from app.agents.schemas import (
    Diagnosis,
    DiagnosisConfidence,
    DiagnosticAnalysis,
    DiagnosticRequest,
    DiagnosticResponse,
    PatientContext,
    ReasoningStep,
    UrgencyAssessment,
)
from app.core.config import settings
from app.core.redis import get_redis_client

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# =============================================================================
# Token Usage Tracking
# =============================================================================


class TokenUsageTracker:
    """Tracks token usage for monitoring and cost analysis."""

    def __init__(self):
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_requests = 0
        self.request_history: list[dict] = []

    def record_usage(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        model: str,
        request_id: str,
    ):
        """Record token usage for a request."""
        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens
        self.total_requests += 1

        # Estimate cost (GPT-4o pricing as of 2024)
        prompt_cost = (prompt_tokens / 1000) * 0.005  # $5 per 1M input
        completion_cost = (completion_tokens / 1000) * 0.015  # $15 per 1M output

        usage_record = {
            "request_id": request_id,
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "estimated_cost_usd": prompt_cost + completion_cost,
        }

        self.request_history.append(usage_record)

        # Keep only last 1000 records in memory
        if len(self.request_history) > 1000:
            self.request_history = self.request_history[-1000:]

        logger.info(
            f"Token usage - Request: {request_id}, "
            f"Prompt: {prompt_tokens}, Completion: {completion_tokens}, "
            f"Cost: ${usage_record['estimated_cost_usd']:.4f}"
        )

        return usage_record

    def get_summary(self) -> dict:
        """Get usage summary."""
        return {
            "total_requests": self.total_requests,
            "total_prompt_tokens": self.total_prompt_tokens,
            "total_completion_tokens": self.total_completion_tokens,
            "total_tokens": self.total_prompt_tokens + self.total_completion_tokens,
        }


# Global token tracker
token_tracker = TokenUsageTracker()


# =============================================================================
# Confidence Score Calibration
# =============================================================================


class ConfidenceCalibrator:
    """Calibrates and adjusts AI confidence scores."""

    # Empirical calibration factors based on validation
    CALIBRATION_FACTORS = {
        "very_high_adjustment": 0.92,  # Slightly reduce very high confidence
        "high_adjustment": 0.95,
        "moderate_adjustment": 1.0,
        "low_adjustment": 1.05,  # Slightly increase low confidence
        "very_low_adjustment": 1.1,
    }

    # Adjust based on data quality
    DATA_QUALITY_FACTORS = {
        "excellent": 1.0,  # >= 0.9
        "good": 0.95,  # 0.7 - 0.9
        "fair": 0.85,  # 0.5 - 0.7
        "poor": 0.7,  # < 0.5
    }

    @classmethod
    def calibrate_confidence(
        cls,
        raw_confidence: float,
        data_quality: float,
        num_supporting_evidence: int,
    ) -> float:
        """
        Calibrate raw confidence score.

        Args:
            raw_confidence: Original confidence from model
            data_quality: Quality score of input data
            num_supporting_evidence: Number of supporting evidence items

        Returns:
            Calibrated confidence score
        """
        # Apply category-based adjustment
        if raw_confidence >= 0.8:
            adjustment = cls.CALIBRATION_FACTORS["very_high_adjustment"]
        elif raw_confidence >= 0.6:
            adjustment = cls.CALIBRATION_FACTORS["high_adjustment"]
        elif raw_confidence >= 0.4:
            adjustment = cls.CALIBRATION_FACTORS["moderate_adjustment"]
        elif raw_confidence >= 0.2:
            adjustment = cls.CALIBRATION_FACTORS["low_adjustment"]
        else:
            adjustment = cls.CALIBRATION_FACTORS["very_low_adjustment"]

        calibrated = raw_confidence * adjustment

        # Apply data quality factor
        if data_quality >= 0.9:
            quality_factor = cls.DATA_QUALITY_FACTORS["excellent"]
        elif data_quality >= 0.7:
            quality_factor = cls.DATA_QUALITY_FACTORS["good"]
        elif data_quality >= 0.5:
            quality_factor = cls.DATA_QUALITY_FACTORS["fair"]
        else:
            quality_factor = cls.DATA_QUALITY_FACTORS["poor"]

        calibrated *= quality_factor

        # Boost slightly if many supporting evidence items
        if num_supporting_evidence >= 5:
            calibrated *= 1.05
        elif num_supporting_evidence >= 3:
            calibrated *= 1.02

        # Ensure within bounds
        return max(0.01, min(0.99, calibrated))

    @classmethod
    def get_confidence_category(cls, score: float) -> DiagnosisConfidence:
        """Get categorical confidence level."""
        if score < 0.2:
            return DiagnosisConfidence.VERY_LOW
        elif score < 0.4:
            return DiagnosisConfidence.LOW
        elif score < 0.6:
            return DiagnosisConfidence.MODERATE
        elif score < 0.8:
            return DiagnosisConfidence.HIGH
        else:
            return DiagnosisConfidence.VERY_HIGH


# =============================================================================
# Response Parser
# =============================================================================


class DiagnosticResponseParser:
    """Parses and validates diagnostic responses from LLM."""

    def __init__(self):
        self.icd_validator = get_icd10_validator()

    def parse_response(
        self,
        raw_response: dict,
        request_id: str,
        case_id: str | None,
        model_version: str,
        processing_time_ms: int,
        tokens_used: int | None,
    ) -> DiagnosticAnalysis:
        """
        Parse and validate LLM response into DiagnosticAnalysis.

        Args:
            raw_response: Raw JSON response from LLM
            request_id: Unique request identifier
            case_id: Associated case ID
            model_version: Model version used
            processing_time_ms: Processing time in milliseconds
            tokens_used: Total tokens used

        Returns:
            Validated DiagnosticAnalysis object
        """
        try:
            # Extract and validate differential diagnosis
            diagnoses = self._parse_diagnoses(raw_response.get("differential_diagnosis", []))

            # Validate ICD-10 codes
            diagnoses = self._validate_icd_codes(diagnoses)

            # Parse reasoning chain
            reasoning_chain = self._parse_reasoning_chain(raw_response.get("reasoning_chain", []))

            # Parse urgency assessment
            urgency = self._parse_urgency(raw_response.get("urgency_assessment", {}))

            # Calculate data quality score
            data_quality = raw_response.get("data_quality_score", 0.7)

            # Calibrate confidence scores
            for dx in diagnoses:
                dx.confidence_score = ConfidenceCalibrator.calibrate_confidence(
                    dx.confidence_score,
                    data_quality,
                    len(dx.supporting_evidence),
                )
                dx.confidence_category = ConfidenceCalibrator.get_confidence_category(
                    dx.confidence_score
                )

            # Identify primary diagnosis
            primary_diagnosis = None
            if diagnoses:
                # Sort by probability and mark primary
                diagnoses.sort(key=lambda x: x.probability, reverse=True)
                diagnoses[0].is_primary = True
                primary_diagnosis = diagnoses[0]

            # Build analysis object
            analysis = DiagnosticAnalysis(
                analysis_id=request_id,
                case_id=case_id,
                model_version=model_version,
                analysis_timestamp=datetime.now(),
                patient_summary=raw_response.get("patient_summary", ""),
                differential_diagnosis=diagnoses,
                primary_diagnosis=primary_diagnosis,
                reasoning_chain=reasoning_chain,
                clinical_summary=raw_response.get("clinical_summary", ""),
                urgency_assessment=urgency,
                immediate_actions=raw_response.get("immediate_actions", []),
                additional_history_needed=raw_response.get("additional_history_needed", []),
                overall_confidence=raw_response.get("overall_confidence", 0.5),
                data_quality_score=data_quality,
                tokens_used=tokens_used,
                processing_time_ms=processing_time_ms,
            )

            return analysis

        except Exception as e:
            logger.error(f"Failed to parse diagnostic response: {e}")
            raise ValueError(f"Failed to parse diagnostic response: {e}")

    def _parse_diagnoses(self, raw_diagnoses: list) -> list[Diagnosis]:
        """Parse diagnosis list."""
        diagnoses = []

        for raw_dx in raw_diagnoses:
            try:
                dx = Diagnosis(
                    name=raw_dx.get("name", "Unknown"),
                    icd10_code=raw_dx.get("icd10_code", "R69"),
                    icd10_description=raw_dx.get("icd10_description", "Unknown diagnosis"),
                    probability=float(raw_dx.get("probability", 0.0)),
                    confidence_score=float(raw_dx.get("confidence_score", 0.5)),
                    confidence_category=raw_dx.get("confidence_category", "moderate"),
                    clinical_reasoning=raw_dx.get("clinical_reasoning", ""),
                    supporting_evidence=[],  # Will be parsed
                    contradicting_evidence=[],
                    suggested_tests=[],
                    is_primary=raw_dx.get("is_primary", False),
                    category=raw_dx.get("category", "Unknown"),
                )

                # Parse evidence
                for evidence in raw_dx.get("supporting_evidence", []):
                    dx.supporting_evidence.append(evidence)

                for evidence in raw_dx.get("contradicting_evidence", []):
                    dx.contradicting_evidence.append(evidence)

                for test in raw_dx.get("suggested_tests", []):
                    dx.suggested_tests.append(test)

                diagnoses.append(dx)

            except Exception as e:
                logger.warning(f"Failed to parse diagnosis: {e}")
                continue

        return diagnoses

    def _validate_icd_codes(self, diagnoses: list[Diagnosis]) -> list[Diagnosis]:
        """Validate and potentially correct ICD-10 codes."""
        for dx in diagnoses:
            is_valid, message = self.icd_validator.validate_code(dx.icd10_code)

            if not is_valid:
                # Try to find a valid code
                suggestions = self.icd_validator.suggest_code(dx.name)
                if suggestions:
                    dx.icd10_code = suggestions[0].code
                    dx.icd10_description = suggestions[0].description
                    logger.info(f"Corrected ICD-10 code for {dx.name}: {dx.icd10_code}")

        return diagnoses

    def _parse_reasoning_chain(self, raw_chain: list) -> list[ReasoningStep]:
        """Parse reasoning chain."""
        steps = []

        for raw_step in raw_chain:
            try:
                step = ReasoningStep(
                    step_number=raw_step.get("step_number", len(steps) + 1),
                    observation=raw_step.get("observation", ""),
                    inference=raw_step.get("inference", ""),
                    hypothesis_impact=raw_step.get("hypothesis_impact", ""),
                    confidence_delta=float(raw_step.get("confidence_delta", 0.0)),
                )
                steps.append(step)
            except Exception as e:
                logger.warning(f"Failed to parse reasoning step: {e}")
                continue

        return steps

    def _parse_urgency(self, raw_urgency: dict) -> UrgencyAssessment:
        """Parse urgency assessment."""
        return UrgencyAssessment(
            level=raw_urgency.get("level", "medium"),
            score=float(raw_urgency.get("score", 0.5)),
            reasoning=raw_urgency.get("reasoning", ""),
            red_flags=raw_urgency.get("red_flags", []),
            recommended_timeframe=raw_urgency.get("recommended_timeframe", "Days"),
            recommended_setting=raw_urgency.get("recommended_setting", "Primary care"),
        )


# =============================================================================
# Main Diagnostic Agent
# =============================================================================


class DiagnosticAgent:
    """
    AI-powered medical diagnostic agent using GPT-4o.

    Features:
    - Medical reasoning with chain-of-thought
    - Differential diagnosis generation
    - ICD-10 code assignment and validation
    - Confidence score calibration
    - Response caching
    - Retry logic with exponential backoff
    - Token usage tracking
    """

    DEFAULT_MODEL = "gpt-4o"
    CACHE_TTL = 3600  # 1 hour
    MAX_RETRIES = 3

    def __init__(
        self,
        model: str = None,
        temperature: float = 0.1,
        api_key: str = None,
    ):
        """
        Initialize diagnostic agent.

        Args:
            model: OpenAI model to use
            temperature: Sampling temperature (lower = more deterministic)
            api_key: OpenAI API key (defaults to settings)
        """
        self.model = model or self.DEFAULT_MODEL
        self.temperature = temperature
        self.api_key = api_key or settings.OPENAI_API_KEY

        # Initialize LangChain LLM with JSON mode
        self.llm = ChatOpenAI(
            model=self.model,
            temperature=self.temperature,
            api_key=self.api_key,
            model_kwargs={"response_format": {"type": "json_object"}},
        )

        # Initialize components
        self.prompt_template = get_diagnostic_prompt_template()
        self.parser = DiagnosticResponseParser()
        self.redis_client = None  # Will be initialized on first use

        logger.info(f"DiagnosticAgent initialized with model: {self.model}")

    async def _get_redis(self):
        """Get Redis client for caching."""
        if self.redis_client is None:
            self.redis_client = await get_redis_client()
        return self.redis_client

    def _generate_cache_key(self, request: DiagnosticRequest) -> str:
        """Generate cache key for request."""
        # Create hash of relevant request data
        cache_data = {
            "patient": request.patient.model_dump(),
            "max_diagnoses": request.max_diagnoses,
        }

        data_str = json.dumps(cache_data, sort_keys=True)
        hash_key = hashlib.sha256(data_str.encode()).hexdigest()[:32]

        return f"diagnostic:cache:{hash_key}"

    async def _get_cached_response(self, cache_key: str) -> DiagnosticAnalysis | None:
        """Get cached response if available."""
        try:
            redis = await self._get_redis()
            if redis is None:
                return None

            cached = await redis.get(cache_key)
            if cached:
                data = json.loads(cached)
                logger.info(f"Cache hit for key: {cache_key}")
                return DiagnosticAnalysis(**data)
        except Exception as e:
            logger.warning(f"Cache retrieval failed: {e}")

        return None

    async def _cache_response(
        self,
        cache_key: str,
        analysis: DiagnosticAnalysis,
    ):
        """Cache successful response."""
        try:
            redis = await self._get_redis()
            if redis is None:
                return

            await redis.setex(
                cache_key,
                self.CACHE_TTL,
                analysis.model_dump_json(),
            )
            logger.info(f"Cached response with key: {cache_key}")
        except Exception as e:
            logger.warning(f"Cache storage failed: {e}")

    def _format_patient_context(self, patient: PatientContext) -> dict:
        """Format patient context for prompt."""
        return {
            "age": patient.age,
            "gender": patient.gender,
            "chief_complaint": patient.chief_complaint,
            "symptoms": format_symptoms(patient.symptoms),
            "vital_signs": format_vitals(patient.vital_signs),
            "lab_results": format_labs(patient.lab_results),
            "medical_history": format_history(patient.medical_history),
            "current_medications": format_medications(patient.current_medications),
            "onset_description": patient.onset_description or "Not specified",
            "additional_notes": patient.additional_notes or "None",
        }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((RateLimitError, APIConnectionError)),
    )
    async def _call_llm(self, formatted_prompt: str) -> tuple[dict, int, int]:
        """
        Call LLM with retry logic.

        Returns:
            Tuple of (response_dict, prompt_tokens, completion_tokens)
        """
        try:
            # Invoke the chain
            chain = self.prompt_template | self.llm

            response = await chain.ainvoke(formatted_prompt)

            # Extract token usage from response
            prompt_tokens = 0
            completion_tokens = 0

            if hasattr(response, "response_metadata"):
                usage = response.response_metadata.get("token_usage", {})
                prompt_tokens = usage.get("prompt_tokens", 0)
                completion_tokens = usage.get("completion_tokens", 0)

            # Parse JSON content
            content = response.content
            if isinstance(content, str):
                parsed = json.loads(content)
            else:
                parsed = content

            return parsed, prompt_tokens, completion_tokens

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON response: {e}")
            raise ValueError(f"Invalid JSON response from LLM: {e}")
        except RateLimitError:
            logger.warning("Rate limit hit, retrying...")
            raise
        except APIConnectionError:
            logger.warning("API connection error, retrying...")
            raise
        except APIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise

    async def analyze(
        self,
        request: DiagnosticRequest,
        use_cache: bool = True,
    ) -> DiagnosticResponse:
        """
        Perform diagnostic analysis on patient data.

        Args:
            request: Diagnostic request with patient context
            use_cache: Whether to use cached responses

        Returns:
            DiagnosticResponse with analysis or error
        """
        request_id = str(uuid4())
        start_time = time.time()

        logger.info(f"Starting diagnostic analysis - Request ID: {request_id}")

        try:
            # Check cache
            cache_key = self._generate_cache_key(request)

            if use_cache:
                cached = await self._get_cached_response(cache_key)
                if cached:
                    return DiagnosticResponse(
                        success=True,
                        analysis=cached,
                        cached=True,
                        cache_key=cache_key,
                    )

            # Format patient context
            formatted_context = self._format_patient_context(request.patient)

            # Call LLM
            raw_response, prompt_tokens, completion_tokens = await self._call_llm(formatted_context)

            # Calculate processing time
            processing_time_ms = int((time.time() - start_time) * 1000)

            # Record token usage
            total_tokens = prompt_tokens + completion_tokens
            token_tracker.record_usage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                model=self.model,
                request_id=request_id,
            )

            # Parse response
            analysis = self.parser.parse_response(
                raw_response=raw_response,
                request_id=request_id,
                case_id=request.case_id,
                model_version=self.model,
                processing_time_ms=processing_time_ms,
                tokens_used=total_tokens,
            )

            # Cache successful response
            if use_cache:
                await self._cache_response(cache_key, analysis)

            logger.info(
                f"Diagnostic analysis complete - Request ID: {request_id}, "
                f"Time: {processing_time_ms}ms, Tokens: {total_tokens}"
            )

            return DiagnosticResponse(
                success=True,
                analysis=analysis,
                cached=False,
                cache_key=cache_key,
            )

        except ValidationError as e:
            logger.error(f"Validation error in analysis: {e}")
            return DiagnosticResponse(
                success=False,
                error=f"Validation error: {str(e)}",
            )
        except ValueError as e:
            logger.error(f"Value error in analysis: {e}")
            return DiagnosticResponse(
                success=False,
                error=str(e),
            )
        except Exception as e:
            logger.error(f"Unexpected error in analysis: {e}", exc_info=True)
            return DiagnosticResponse(
                success=False,
                error=f"Analysis failed: {str(e)}",
            )

    async def get_token_usage(self) -> dict:
        """Get token usage statistics."""
        return token_tracker.get_summary()


# =============================================================================
# Factory Function
# =============================================================================


def create_diagnostic_agent(
    model: str = None,
    temperature: float = 0.1,
) -> DiagnosticAgent:
    """
    Create a configured diagnostic agent.

    Args:
        model: OpenAI model to use
        temperature: Sampling temperature

    Returns:
        Configured DiagnosticAgent instance
    """
    return DiagnosticAgent(
        model=model,
        temperature=temperature,
    )
