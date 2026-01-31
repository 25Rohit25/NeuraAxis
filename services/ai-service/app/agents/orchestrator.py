"""
NEURAXIS - Intelligent Orchestrator
Multi-agent workflow manager mimicking LangGraph architecture.
"""

import asyncio
import logging
import time
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

from app.agents.diagnostic import get_diagnostic_agent
from app.agents.drug_interaction import get_drug_interaction_agent
from app.agents.drug_interaction_schemas import DrugInput, InteractionCheckRequest, PatientProfile
from app.agents.orchestrator_schemas import CaseAnalysisRequest, CaseAnalysisResult, WorkflowState
from app.agents.research import get_research_agent
from app.agents.research_schemas import ResearchQuery, ResearchRequest

# from app.agents.documentation import get_documentation_agent # TODO: Implement Documentation Agent
# Input Schemas
from app.agents.schemas import DiagnosticRequest, PatientContext, SymptomInput
from app.agents.treatment import get_treatment_agent
from app.agents.treatment_schemas import DiagnosisInput, PatientDemographics, TreatmentPlanRequest

logger = logging.getLogger(__name__)

# =============================================================================
# Mini-LangGraph Implementation (Polyfill)
# =============================================================================


class StateGraph:
    """
    Lightweight implementation of LangGraph's StateGraph for environment compatibility.
    """

    def __init__(self, state_schema):
        self.state_schema = state_schema
        self.nodes: Dict[str, Callable] = {}
        self.edges: Dict[str, List[str]] = {}
        self.entry_point: str = ""
        self.end_point: str = "END"

    def add_node(self, name: str, action: Callable):
        self.nodes[name] = action
        return self

    def set_entry_point(self, key: str):
        self.entry_point = key
        return self

    def add_edge(self, start_key: str, end_key: str):
        if start_key not in self.edges:
            self.edges[start_key] = []
        self.edges[start_key].append(end_key)
        return self

    def add_conditional_edges(self, start_key: str, condition: Callable, mapping: Dict[str, str]):
        # Simplified: We'll just handle parallel execution explicitly in this implementation
        # For true conditional edges in a custom engine, we'd need a router.
        # This polyfill will implement the specific logic for this workflow.
        pass

    def compile(self):
        return CompiledGraph(self)


class CompiledGraph:
    def __init__(self, graph: StateGraph):
        self.graph = graph

    async def invoke(self, initial_state: WorkflowState) -> WorkflowState:
        """
        Execute the graph.
        Custom logic for the Parallel -> Aggregate -> Serial flow.
        """
        state = initial_state

        # 1. Entry Node (Implicit or explicit steps)
        # We will hardcode the execution flow here for robustness without the full LangGraph engine

        # Step 1: Parallel Execution (Diagnostic, Research, Image)
        results = await asyncio.gather(
            self.graph.nodes["diagnostic_agent"](state),
            self.graph.nodes["research_agent"](state),
            self.graph.nodes["image_agent"](state),
            return_exceptions=True,
        )

        # Merge results into state
        # Note: nodes modify state and return it (or just modification).
        # Since state is an object, modifications persist.
        # But we need to handle exceptions.
        for i, res in enumerate(results):
            if isinstance(res, Exception):
                logger.error(f"Parallel step {i} failed: {res}")
                state.errors.append(str(res))

        state.completed_steps.extend(["diagnostic", "research", "image"])

        # Step 2: Treatment (Depends on Diag + Research)
        if not state.errors:
            try:
                state = await self.graph.nodes["treatment_agent"](state)
                state.completed_steps.append("treatment")
            except Exception as e:
                logger.error(f"Treatment step failed: {e}")
                state.errors.append(str(e))

        # Step 3: Safety (Depends on Treatment)
        if state.treatment_plan and not state.errors:
            try:
                state = await self.graph.nodes["safety_agent"](state)
                state.completed_steps.append("safety")
            except Exception as e:
                logger.error(f"Safety step failed: {e}")
                state.errors.append(str(e))

        # Step 4: Documentation
        if not state.errors:
            try:
                state = await self.graph.nodes["documentation_agent"](state)
                state.completed_steps.append("documentation")
            except Exception as e:
                logger.error(f"Documentation failed: {e}")
                # Warn but don't fail flow?

        return state


# =============================================================================
# Node Implementations
# =============================================================================


async def diagnostic_node(state: WorkflowState) -> WorkflowState:
    """Run Diagnostic Agent."""
    logger.info(f"[{state.case_id}] Running Diagnostic Node")
    try:
        agent = get_diagnostic_agent()

        # Map state to request
        symptoms_input = [SymptomInput(name=s, severity=5) for s in state.symptoms]

        patient = PatientContext(
            age=state.patient_data.get("age"),
            gender=state.patient_data.get("gender"),
            chief_complaint=state.patient_data.get("chief_complaint"),
            symptoms=symptoms_input,
            medical_history=[state.patient_data.get("history", "")],
            current_medications=state.patient_data.get("medications", []),
        )

        req = DiagnosticRequest(patient=patient)

        # Execute
        result = await agent.analyze(req)

        # Update state
        state.diagnostic_result = result
        if not result.success:
            state.errors.append(f"Diagnostic failed: {result.error}")

    except Exception as e:
        logger.error(f"Diagnostic node error: {e}", exc_info=True)
        state.errors.append(f"Diagnostic node crashed: {str(e)}")

    return state


async def research_node(state: WorkflowState) -> WorkflowState:
    """Run Research Agent."""
    logger.info(f"[{state.case_id}] Running Research Node")
    try:
        agent = get_research_agent()

        # Formulate query from symptoms
        query_text = f"Differential diagnosis and treatment for {state.patient_data.get('chief_complaint')} with {', '.join(state.symptoms)}"

        req = ResearchRequest(
            query=ResearchQuery(query=query_text, max_results=5, include_clinical_trials=True)
        )

        # Execute
        result = await agent.research(req)

        # Update state
        state.research_result = result

    except Exception as e:
        logger.error(f"Research node error: {e}", exc_info=True)
        # Non-critical, do not fail workflow
        state.errors.append(f"Research warning: {str(e)}")

    return state


from app.agents.image_analysis import get_image_analysis_agent
from app.agents.image_schemas import ImageAnalysisRequest


async def image_analysis_node(state: WorkflowState) -> WorkflowState:
    """Run Image Analysis Agent."""
    if not state.medical_images:
        return state

    logger.info(f"[{state.case_id}] Running Image Analysis Node")

    try:
        agent = get_image_analysis_agent()

        # For prototype, we analyze the first image
        # In production, we might loop or aggregate
        image_url = state.medical_images[0]

        # Determine modality if possible or default
        # Ideally, this comes from input, but we default to X-Ray for general usage
        req = ImageAnalysisRequest(
            case_id=state.case_id,
            image_url=image_url,
            # modality/body_part defaults are in schema
        )

        result = await agent.analyze_image(req)

        state.image_analysis_result = result.dict()
        state.completed_steps.append("image_analysis")

    except Exception as e:
        logger.error(f"Image analysis node error: {e}", exc_info=True)
        # Non-critical for general workflow if image fails?
        state.errors.append(f"Image analysis failed: {str(e)}")

    return state


async def treatment_node(state: WorkflowState) -> WorkflowState:
    """Run Treatment Agent."""
    logger.info(f"[{state.case_id}] Running Treatment Node")

    if not state.diagnostic_result or not state.diagnostic_result.primary_diagnosis:
        msg = "Skipping treatment: No primary diagnosis found"
        logger.warning(msg)
        state.errors.append(msg)
        return state

    try:
        agent = get_treatment_agent()

        diagnosis_name = state.diagnostic_result.primary_diagnosis.name
        icd_code = state.diagnostic_result.primary_diagnosis.icd10_code or "R69"

        # Map patient data
        p_data = state.patient_data
        patient = PatientDemographics(
            age=p_data.get("age"),
            gender=p_data.get("gender"),
            weight_kg=p_data.get("weight_kg", 70),  # Default if missing
        )

        # Map inputs
        req = TreatmentPlanRequest(
            case_id=state.case_id,
            diagnosis=DiagnosisInput(name=diagnosis_name, icd10_code=icd_code),
            patient=patient,
            current_medications=[],  # TODO: map from input
            conditions=[],  # TODO: map from history/input
        )

        # Execute
        result = await agent.generate_plan(req)

        state.treatment_plan = result

    except Exception as e:
        logger.error(f"Treatment node error: {e}", exc_info=True)
        state.errors.append(f"Treatment node failed: {str(e)}")

    return state


async def safety_node(state: WorkflowState) -> WorkflowState:
    """Run Drug Interaction Agent."""
    logger.info(f"[{state.case_id}] Running Safety Checker Node")

    if not state.treatment_plan or not state.treatment_plan.plan:
        return state  # Nothing to check

    try:
        agent = get_drug_interaction_agent()

        # Extract meds from plan
        proposed_meds = []
        for med in state.treatment_plan.plan.first_line_medications:
            proposed_meds.append(DrugInput(drug_name=med.generic_name, dose=med.dose))

        current_meds = []  # From patient history

        p = state.patient_data
        profile = PatientProfile(
            age=p.get("age"),
            gender=p.get("gender"),
            current_medications=current_meds,
            allergies=p.get("allergies", []),
        )

        req = InteractionCheckRequest(drugs_to_check=proposed_meds, patient_profile=profile)

        # Execute
        result = await agent.check_interactions(req)

        state.safety_cbeck = result

    except Exception as e:
        logger.error(f"Safety node error: {e}", exc_info=True)
        state.errors.append(f"Safety checked failed: {str(e)}")

    return state


from app.agents.documentation import get_documentation_agent
from app.agents.documentation_schemas import DocumentationRequest, NoteType, VisitType


async def documentation_node(state: WorkflowState) -> WorkflowState:
    """Generate notes."""
    logger.info(f"[{state.case_id}] Running Documentation Node")

    try:
        agent = get_documentation_agent()

        # Determine inputs
        # We need Diagnosis and Treatment Plan from state

        dx_data = state.diagnostic_result.dict() if state.diagnostic_result else {}
        rx_data = state.treatment_plan.dict() if state.treatment_plan else {}

        # Construct Request
        # Defaulting to SOAP Note for generic workflow
        req = DocumentationRequest(
            case_id=state.case_id,
            patient_id=state.user_id or "unknown",
            visit_type=VisitType.NEW_PATIENT,  # Default
            note_type=NoteType.SOAP,  # Default
            chief_complaint=state.patient_data.get("chief_complaint", "Unknown"),
            hpi=state.initial_notes or "See symptoms.",
            diagnosis_data=dx_data,
            treatment_plan=rx_data,
            lab_results=state.patient_data.get("lab_results", {}),
        )

        result = await agent.generate_documentation(req)

        # Store result
        state.documentation = result.content
        state.documentation_result = result.dict()
        state.completed_steps.append("documentation")

    except Exception as e:
        logger.error(f"Documentation failed: {e}", exc_info=True)
        # Warn but don't fail flow?
        state.errors.append(f"Documentation failed: {str(e)}")

    return state


# =============================================================================
# Orchestrator Class
# =============================================================================


class Orchestrator:
    """
    Main entry point for running the multi-agent graph.
    """

    def __init__(self):
        self.graph = StateGraph(WorkflowState)
        self._build_graph()
        self.runner = self.graph.compile()

    def _build_graph(self):
        """Define the graph structure."""
        self.graph.add_node("diagnostic_agent", diagnostic_node)
        self.graph.add_node("research_agent", research_node)
        self.graph.add_node("image_agent", image_analysis_node)
        self.graph.add_node("treatment_agent", treatment_node)
        self.graph.add_node("safety_agent", safety_node)
        self.graph.add_node("documentation_agent", documentation_node)

        # Edges are implicit in the custom 'compile().invoke()' method
        # for this polyfill implementation.
        # In real LangGraph, we would define them here:
        # self.graph.add_edge("entry", "diagnostic_agent")
        # ...

    async def run_analysis(self, request: CaseAnalysisRequest) -> WorkflowState:
        """Run the full analysis workflow."""
        start_time = time.time()

        # Initialize State
        initial_state = WorkflowState(
            case_id=request.case_id or str(uuid4()),
            user_id="system",  # TODO: pass user context
            start_time=start_time,
            patient_data={
                "age": request.patient_age,
                "gender": request.patient_gender,
                "chief_complaint": request.chief_complaint,
                "history": request.history,
                "medications": request.medications,
                "allergies": [],  # TODO: add to request model
                "weight_kg": 70,  # TODO: add to request model
            },
            symptoms=request.symptoms,
            medical_images=request.image_urls,
        )

        # Run Graph
        final_state = await self.runner.invoke(initial_state)

        total_time = time.time() - start_time
        logger.info(f"Analysis completed in {total_time:.2f}s")

        return final_state


# Singleton
_orchestrator = Orchestrator()


def get_orchestrator() -> Orchestrator:
    return _orchestrator
