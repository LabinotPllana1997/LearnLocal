"""
LearnerExpert LangGraph Multi-Agent System

Orchestrates the workflow between agents for curriculum validation, quiz creation,
content enrichment, and feedback evaluation using LangGraph.
"""

import logging
from typing import Dict, Any, Optional
from uuid import uuid4

from langgraph.graph import StateGraph, START, END
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver

from learnerexpert.agents.states import (
    LearnerExpertState, 
    WorkflowStage, 
    AgentNames, 
    AgentStatus,
    create_initial_state
)
from learnerexpert.agents.tools import ALL_TOOLS
from learnerexpert.config.settings import get_settings

logger = logging.getLogger(__name__)

# Module-level graph instance
_graph: Optional[CompiledStateGraph] = None
_checkpointer = MemorySaver()


def route_to_next_agent(state: LearnerExpertState) -> str:
    """
    Route to the next agent based on current workflow stage.
    
    This is the core routing logic that determines which agent should
    execute next based on the current state and workflow stage.
    """
    current_stage = state["workflow_stage"]
    current_agent = state.get("current_agent")
    completed_agents = state.get("completed_agents", [])
    errors = state.get("errors", [])
    
    logger.debug(
        f"Routing decision: stage={current_stage}, "
        f"agent={current_agent}, completed={len(completed_agents)}"
    )
    
    # Check for errors that should terminate workflow
    critical_errors = [e for e in errors if e.get("type") == "critical"]
    if critical_errors:
        logger.error(f"Critical errors found, terminating workflow")
        return "__end__"
    
    # Check iteration limit
    max_iterations = state.get("max_iterations", 10)
    if len(completed_agents) >= max_iterations:
        logger.warning("Max iterations reached, terminating workflow")
        return "__end__"
    
    # Route based on workflow stage
    routing_map = {
        WorkflowStage.INITIALIZE: AgentNames.CURRICULUM_VALIDATOR,
        WorkflowStage.VALIDATE: AgentNames.QUIZ_CREATOR,
        WorkflowStage.QUIZ: AgentNames.CONTENT_ENRICHER,
        WorkflowStage.ENRICH: AgentNames.FEEDBACK_EVALUATOR,
        WorkflowStage.FEEDBACK: AgentNames.MEMORY,
        WorkflowStage.MEMORY: "__end__",
        WorkflowStage.COMPLETE: "__end__",
        WorkflowStage.ERROR: "__end__"
    }
    
    next_destination = routing_map.get(current_stage, "__end__")
    
    logger.debug(f"Routing to: {next_destination}")
    return next_destination


def should_use_tools(state: LearnerExpertState) -> str:
    """
    Determine if the current agent should use tools.
    
    Based on the last message and agent context, decide whether to
    route to tools or continue with the workflow.
    """
    messages = state.get("messages", [])
    current_agent = state.get("current_agent")
    tool_call_count = state.get("tool_call_count", 0)
    
    # Prevent infinite tool loops
    if tool_call_count >= 3:
        logger.warning(f"Tool call limit reached ({tool_call_count}), skipping tools")
        return "continue"
    
    # Check if last message has tool calls
    if messages:
        last_message = messages[-1]
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            logger.debug(f"Agent {current_agent} requested {len(last_message.tool_calls)} tools")
            return "tools"
    
    # Default to continuing workflow
    return "continue"


def build_learner_graph() -> StateGraph:
    """
    Build the LearnerExpert multi-agent graph.
    
    Creates a StateGraph with all agents and their connections,
    implementing the workflow defined in the user journey documentation.
    """
    logger.info("Building LearnerExpert multi-agent graph")
    
    # Import agent functions (will be created in next steps)
    from learnerexpert.agents.nodes.orchestrator import orchestrator_agent
    from learnerexpert.agents.nodes.curriculum_validator import curriculum_validator_agent
    from learnerexpert.agents.nodes.quiz_creator import quiz_creator_agent
    from learnerexpert.agents.nodes.content_enricher import content_enricher_agent
    from learnerexpert.agents.nodes.feedback_evaluator import feedback_evaluator_agent
    from learnerexpert.agents.nodes.memory import memory_agent
    
    # Create the state graph
    builder = StateGraph(LearnerExpertState)
    
    # Add all agent nodes
    builder.add_node(AgentNames.ORCHESTRATOR, orchestrator_agent)
    builder.add_node(AgentNames.CURRICULUM_VALIDATOR, curriculum_validator_agent)
    builder.add_node(AgentNames.QUIZ_CREATOR, quiz_creator_agent)
    builder.add_node(AgentNames.CONTENT_ENRICHER, content_enricher_agent)
    builder.add_node(AgentNames.FEEDBACK_EVALUATOR, feedback_evaluator_agent)
    builder.add_node(AgentNames.MEMORY, memory_agent)
    
    # Add tools node for all agents to use
    builder.add_node("tools", ToolNode(ALL_TOOLS))
    
    # Define the workflow edges
    # Start with orchestrator
    builder.add_edge(START, AgentNames.ORCHESTRATOR)
    
    # Orchestrator routes to the appropriate next agent
    builder.add_conditional_edges(
        AgentNames.ORCHESTRATOR,
        route_to_next_agent,
        {
            AgentNames.CURRICULUM_VALIDATOR: AgentNames.CURRICULUM_VALIDATOR,
            AgentNames.QUIZ_CREATOR: AgentNames.QUIZ_CREATOR,
            AgentNames.CONTENT_ENRICHER: AgentNames.CONTENT_ENRICHER,
            AgentNames.FEEDBACK_EVALUATOR: AgentNames.FEEDBACK_EVALUATOR,
            AgentNames.MEMORY: AgentNames.MEMORY,
            "__end__": END
        }
    )
    
    # Each agent can use tools or continue to next agent via orchestrator
    for agent_name in [
        AgentNames.CURRICULUM_VALIDATOR,
        AgentNames.QUIZ_CREATOR, 
        AgentNames.CONTENT_ENRICHER,
        AgentNames.FEEDBACK_EVALUATOR,
        AgentNames.MEMORY
    ]:
        # Agent to tools or orchestrator
        builder.add_conditional_edges(
            agent_name,
            should_use_tools,
            {
                "tools": "tools",
                "continue": AgentNames.ORCHESTRATOR
            }
        )
    
    # Tools always return to the calling agent (handled by ToolNode)
    # But we need to explicitly route back to orchestrator after tools
    builder.add_edge("tools", AgentNames.ORCHESTRATOR)
    
    logger.info("LearnerExpert graph built successfully")
    return builder


def get_graph() -> CompiledStateGraph:
    """
    Get or create the compiled LearnerExpert graph.
    
    Returns a singleton instance of the compiled graph with checkpointing enabled.
    """
    global _graph, _checkpointer
    
    if _graph is None:
        logger.info("Compiling LearnerExpert graph for first time")
        
        try:
            # Build the graph
            builder = build_learner_graph()
            
            # Compile with memory checkpointing
            _graph = builder.compile(checkpointer=_checkpointer)
            
            logger.info("✅ LearnerExpert graph compiled successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to compile graph: {e}")
            raise
    
    return _graph


async def run_workflow(
    user_id: str,
    session_id: str,
    input_document: str,
    company_okrs: str = "",
    industry: str = "Technology",
    **kwargs
) -> Dict[str, Any]:
    """
    Run the complete LearnerExpert workflow.
    
    Args:
        user_id: Unique identifier for the user
        session_id: Session identifier for tracking
        input_document: Curriculum content to analyze
        company_okrs: Company objectives and key results
        industry: Industry context
        **kwargs: Additional configuration options
        
    Returns:
        Dict containing all workflow results
    """
    logger.info(f"Starting workflow for user {user_id}, session {session_id}")
    
    try:
        # Create initial state
        initial_state = create_initial_state(
            user_id=user_id,
            session_id=session_id,
            input_document=input_document,
            company_okrs=company_okrs,
            industry=industry,
            **kwargs
        )
        
        # Get compiled graph
        graph = get_graph()
        
        # Run the workflow with checkpointing
        config = {
            "configurable": {
                "thread_id": session_id,
                "user_id": user_id
            }
        }
        
        logger.info("Executing LearnerExpert workflow...")
        final_state = await graph.ainvoke(initial_state, config)
        
        # Extract results
        results = {
            "session_id": session_id,
            "user_id": user_id,
            "status": "completed" if not final_state.get("errors") else "completed_with_errors",
            "curriculum_analysis": final_state.get("curriculum_analysis"),
            "gap_matrix": final_state.get("gap_matrix", []),
            "quiz_items": final_state.get("quiz_items", []),
            "enrichment_content": final_state.get("enrichment_content", {}),
            "evaluation_results": final_state.get("evaluation_results"),
            "completed_agents": final_state.get("completed_agents", []),
            "errors": final_state.get("errors", []),
            "warnings": final_state.get("warnings", []),
            "processing_time": final_state.get("processing_time"),
            "agent_timings": final_state.get("agent_timings", {}),
            "token_usage": final_state.get("token_usage", {})
        }
        
        logger.info(f"✅ Workflow completed successfully for session {session_id}")
        logger.info(f"Completed agents: {len(results['completed_agents'])}")
        logger.info(f"Generated {len(results['quiz_items'])} quiz items")
        logger.info(f"Found {len(results['gap_matrix'])} curriculum gaps")
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Workflow failed for session {session_id}: {e}")
        return {
            "session_id": session_id,
            "user_id": user_id,
            "status": "failed",
            "error": str(e),
            "curriculum_analysis": None,
            "gap_matrix": [],
            "quiz_items": [],
            "enrichment_content": {},
            "evaluation_results": None,
            "completed_agents": [],
            "errors": [{"message": str(e), "type": "critical"}],
            "warnings": [],
            "processing_time": None,
            "agent_timings": {},
            "token_usage": {}
        }


def get_workflow_status(session_id: str) -> Dict[str, Any]:
    """
    Get the current status of a workflow session.
    
    Args:
        session_id: Session identifier to check
        
    Returns:
        Dict containing current workflow status
    """
    try:
        graph = get_graph()
        
        # Get current state from checkpointer
        config = {"configurable": {"thread_id": session_id}}
        
        # This would require accessing the checkpointer state
        # For now, return a placeholder
        return {
            "session_id": session_id,
            "status": "unknown",
            "current_stage": "unknown",
            "completed_agents": [],
            "message": "Status checking not yet implemented"
        }
        
    except Exception as e:
        logger.error(f"Failed to get workflow status for {session_id}: {e}")
        return {
            "session_id": session_id,
            "status": "error",
            "error": str(e)
        }


def reset_graph():
    """Reset the global graph instance (useful for testing)."""
    global _graph, _checkpointer
    _graph = None
    _checkpointer = MemorySaver()
    logger.info("Graph reset successfully")


# Graph visualization helper (for development/debugging)
def get_graph_visualization() -> str:
    """Get a text representation of the graph structure."""
    try:
        graph = get_graph()
        # This would create a visualization of the graph
        # For now, return a description
        return """
LearnerExpert Multi-Agent Workflow:

START -> Orchestrator -> {
    Curriculum Validator -> [tools] -> Orchestrator
    Quiz Creator -> [tools] -> Orchestrator  
    Content Enricher -> [tools] -> Orchestrator
    Feedback Evaluator -> [tools] -> Orchestrator
    Memory Agent -> [tools] -> Orchestrator
} -> END

Tools Available:
- OKR Validator Tool
- Gap Analyzer Tool
- Quiz Builder Tool
- Content Finder Tool
"""
    except Exception as e:
        return f"Failed to generate visualization: {e}"