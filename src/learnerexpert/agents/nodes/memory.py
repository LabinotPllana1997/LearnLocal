"""Memory agent for session management."""

from typing import Dict, Any
from learnerexpert.agents.states import LearnerExpertState

async def memory_agent(state: LearnerExpertState) -> Dict[str, Any]:
    """Manages memory and session persistence."""
    return {"current_agent": "memory"}