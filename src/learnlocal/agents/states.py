"""
State definitions for LearnerExpert multi-agent system.

Defines the shared state structure that flows between agents in the LangGraph workflow.
"""

from typing import Annotated, Dict, List, Any, Optional, TypedDict
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph.message import add_messages


class LearnerExpertState(TypedDict):
    """State for LearnerExpert agent communication system."""
    
    # Core messaging
    messages: Annotated[List[HumanMessage | AIMessage | SystemMessage], add_messages]
    
    # Session management
    user_id: str
    session_id: str
    run_id: Optional[str]
    
    # Input data
    input_document: Optional[str]  # Raw curriculum content
    document_type: Optional[str]   # pdf, docx, txt, voice, etc.
    company_okrs: Optional[str]    # Company objectives and key results
    industry: Optional[str]        # Industry context
    target_audience: Optional[str] # Learner demographics
    
    # Workflow control
    current_agent: Optional[str]   # Currently active agent
    workflow_stage: str           # validate, quiz, enrich, feedback, complete
    agent_sequence: List[str]     # Planned agent execution order
    completed_agents: List[str]   # Successfully completed agents
    tool_call_count: int          # Track tool usage to prevent loops
    max_iterations: int           # Safety limit for workflow
    
    # Analysis results
    curriculum_analysis: Optional[Dict[str, Any]]  # CV agent results
    gap_matrix: List[Dict[str, Any]]              # Identified gaps
    alignment_score: Optional[float]              # OKR alignment score
    coverage_analysis: Optional[Dict[str, Any]]   # Topic coverage assessment
    
    # Quiz generation
    quiz_items: List[Dict[str, Any]]              # Generated quiz questions
    quiz_metadata: Optional[Dict[str, Any]]       # Quiz settings and stats
    difficulty_distribution: Optional[Dict[str, int]]  # Question difficulty breakdown
    
    # Content enrichment
    enrichment_content: Dict[str, Any]            # Additional materials
    case_studies: List[Dict[str, Any]]           # Suggested case studies
    hands_on_labs: List[Dict[str, Any]]          # Lab exercises
    reading_materials: List[Dict[str, Any]]      # External resources
    
    # Feedback and evaluation
    feedback_data: Optional[str]                  # Input feedback text
    evaluation_results: Optional[Dict[str, Any]]  # FA agent analysis
    improvement_suggestions: List[str]           # Recommended improvements
    quality_scores: Optional[Dict[str, float]]   # Content quality metrics
    
    # Memory and preferences
    educator_preferences: Dict[str, Any]         # Stored preferences
    session_history: List[Dict[str, Any]]       # Previous interactions
    curriculum_cache: Dict[str, Any]            # Cached curriculum data
    
    # Output configuration
    output_formats: List[str]                    # Requested output types
    export_settings: Dict[str, Any]             # Format-specific settings
    
    # Error handling
    errors: List[Dict[str, Any]]                # Captured errors
    warnings: List[str]                         # Non-fatal issues
    agent_status: Dict[str, str]               # Per-agent status tracking
    
    # Performance metrics
    processing_time: Optional[float]            # Total processing time
    agent_timings: Dict[str, float]            # Per-agent execution time
    token_usage: Dict[str, int]                # LLM token consumption


class WorkflowStage:
    """Constants for workflow stages."""
    
    INITIALIZE = "initialize"
    VALIDATE = "validate"
    QUIZ = "quiz"
    ENRICH = "enrich"
    FEEDBACK = "feedback"
    MEMORY = "memory"
    COMPLETE = "complete"
    ERROR = "error"


class AgentNames:
    """Constants for agent names."""
    
    ORCHESTRATOR = "orchestrator"
    CURRICULUM_VALIDATOR = "curriculum_validator"
    QUIZ_CREATOR = "quiz_creator"
    CONTENT_ENRICHER = "content_enricher"
    FEEDBACK_EVALUATOR = "feedback_evaluator"
    MEMORY = "memory"


class AgentStatus:
    """Constants for agent execution status."""
    
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


def create_initial_state(
    user_id: str,
    session_id: str,
    input_document: str = "",
    company_okrs: str = "",
    industry: str = "Technology",
    **kwargs
) -> LearnerExpertState:
    """Create initial state for a new workflow execution."""
    
    return LearnerExpertState(
        # Core messaging
        messages=[],
        
        # Session management
        user_id=user_id,
        session_id=session_id,
        run_id=None,
        
        # Input data
        input_document=input_document,
        document_type=kwargs.get("document_type", "text"),
        company_okrs=company_okrs,
        industry=industry,
        target_audience=kwargs.get("target_audience", "General"),
        
        # Workflow control
        current_agent=AgentNames.ORCHESTRATOR,
        workflow_stage=WorkflowStage.INITIALIZE,
        agent_sequence=[
            AgentNames.ORCHESTRATOR,
            AgentNames.CURRICULUM_VALIDATOR,
            AgentNames.QUIZ_CREATOR,
            AgentNames.CONTENT_ENRICHER,
            AgentNames.FEEDBACK_EVALUATOR,
            AgentNames.MEMORY
        ],
        completed_agents=[],
        tool_call_count=0,
        max_iterations=kwargs.get("max_iterations", 10),
        
        # Analysis results
        curriculum_analysis=None,
        gap_matrix=[],
        alignment_score=None,
        coverage_analysis=None,
        
        # Quiz generation
        quiz_items=[],
        quiz_metadata=None,
        difficulty_distribution=None,
        
        # Content enrichment
        enrichment_content={},
        case_studies=[],
        hands_on_labs=[],
        reading_materials=[],
        
        # Feedback and evaluation
        feedback_data=None,
        evaluation_results=None,
        improvement_suggestions=[],
        quality_scores=None,
        
        # Memory and preferences
        educator_preferences=kwargs.get("preferences", {}),
        session_history=[],
        curriculum_cache={},
        
        # Output configuration
        output_formats=kwargs.get("output_formats", ["csv", "json", "html"]),
        export_settings=kwargs.get("export_settings", {}),
        
        # Error handling
        errors=[],
        warnings=[],
        agent_status={
            agent: AgentStatus.PENDING 
            for agent in [
                AgentNames.ORCHESTRATOR,
                AgentNames.CURRICULUM_VALIDATOR,
                AgentNames.QUIZ_CREATOR,
                AgentNames.CONTENT_ENRICHER,
                AgentNames.FEEDBACK_EVALUATOR,
                AgentNames.MEMORY
            ]
        },
        
        # Performance metrics
        processing_time=None,
        agent_timings={},
        token_usage={}
    )


def update_agent_status(
    state: LearnerExpertState, 
    agent_name: str, 
    status: str
) -> Dict[str, Any]:
    """Helper to update agent status in state."""
    
    new_agent_status = state["agent_status"].copy()
    new_agent_status[agent_name] = status
    
    return {"agent_status": new_agent_status}


def add_error(
    state: LearnerExpertState,
    error_message: str,
    agent_name: str = None,
    error_type: str = "general"
) -> Dict[str, Any]:
    """Helper to add error to state."""
    
    error_entry = {
        "message": error_message,
        "agent": agent_name,
        "type": error_type,
        "timestamp": None  # Would add datetime in real implementation
    }
    
    new_errors = state["errors"].copy()
    new_errors.append(error_entry)
    
    return {"errors": new_errors}


def add_warning(
    state: LearnerExpertState,
    warning_message: str
) -> Dict[str, Any]:
    """Helper to add warning to state."""
    
    new_warnings = state["warnings"].copy()
    new_warnings.append(warning_message)
    
    return {"warnings": new_warnings}