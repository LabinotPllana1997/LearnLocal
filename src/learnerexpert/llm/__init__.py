"""LLM integration module for OpenAI client and offline model management."""

from .client import get_openai_client
from .offline_model_manager import get_model_manager, OfflineModelManager

__all__ = ["get_openai_client", "get_model_manager", "OfflineModelManager"]