"""Quiz creator agent."""

from typing import Dict, Any
from learnlocal.agents.states import LearnerExpertState

async def quiz_creator_agent(state: LearnerExpertState) -> Dict[str, Any]:
    """Creates quiz questions based on curriculum content."""
    return {"current_agent": "quiz_creator"}