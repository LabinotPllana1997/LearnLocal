"""Orchestrator agent for workflow coordination."""

from typing import Dict, Any
from learnerexpert.agents.states import LearnerExpertState

async def orchestrator_agent(state: LearnerExpertState) -> Dict[str, Any]:
    """Orchestrator agent coordinates workflow between other agents."""
    return {"current_agent": "orchestrator"}