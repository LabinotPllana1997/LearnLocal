"""Feedback evaluator agent."""

from typing import Dict, Any
from learnlocal.agents.states import LearnerExpertState

async def feedback_evaluator_agent(state: LearnerExpertState) -> Dict[str, Any]:
    """Evaluates feedback and provides improvement suggestions."""
    return {"current_agent": "feedback_evaluator"}