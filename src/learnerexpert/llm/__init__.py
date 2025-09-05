"""LLM integration module for OpenAI client and prompt management."""

from .client import get_openai_client
from .prompts import PromptTemplates

__all__ = ["get_openai_client", "PromptTemplates"]