"""Content enricher agent."""

from typing import Dict, Any
from learnlocal.agents.states import LearnerExpertState

async def content_enricher_agent(state: LearnerExpertState) -> Dict[str, Any]:
    """Enriches curriculum with additional learning materials."""
    return {"current_agent": "content_enricher"}