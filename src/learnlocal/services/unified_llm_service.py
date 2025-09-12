"""
Unified offline LLM service that supports both Ollama and Transformers backends.
Automatically chooses the best available option for offline model serving.
"""

import logging
from typing import Optional, Dict, Any
from ..config.settings import get_settings
from ..llm.ollama_client import get_ollama_manager
from ..llm.offline_model_manager import get_model_manager

logger = logging.getLogger(__name__)


class UnifiedOfflineLLMService:
    """Unified service that uses Ollama if available, falls back to Transformers."""
    
    def __init__(self):
        self.settings = get_settings()
        self._ollama_manager = None
        self._transformers_manager = None
        self._active_backend = None
        self._initialize_backend()
    
    def _initialize_backend(self):
        """Initialize the best available backend."""
        if self.settings.offline_llm_provider == "ollama":
            self._try_ollama()
        elif self.settings.offline_llm_provider == "transformers":
            self._try_transformers()
        else:
            self._try_ollama() or self._try_transformers()
    
    def _try_ollama(self) -> bool:
        """Try to initialize Ollama backend."""
        try:
            self._ollama_manager = get_ollama_manager(self.settings.ollama_base_url)
            if self._ollama_manager.is_available():
                self._active_backend = "ollama"
                logger.info("Using Ollama backend for offline LLM")
                return True
            else:
                logger.warning("Ollama server not available")
                return False
        except Exception as e:
            logger.warning(f"Failed to initialize Ollama: {e}")
            return False
    
    def _try_transformers(self) -> bool:
        """Try to initialize Transformers backend."""
        try:
            self._transformers_manager = get_model_manager()
            self._active_backend = "transformers"
            logger.info("Using Transformers backend for offline LLM")
            return True
        except Exception as e:
            logger.warning(f"Failed to initialize Transformers: {e}")
            return False
    
    def is_available(self) -> bool:
        """Check if any backend is available."""
        return self._active_backend is not None
    
    def get_backend_info(self) -> Dict[str, Any]:
        """Get information about the active backend."""
        if self._active_backend == "ollama":
            return {
                "backend": "ollama",
                "server_url": self.settings.ollama_base_url,
                "available": self._ollama_manager.is_available() if self._ollama_manager else False,
                "models": self._ollama_manager.client.list_models() if self._ollama_manager else []
            }
        elif self._active_backend == "transformers":
            return {
                "backend": "transformers",
                "model_info": self._transformers_manager.get_model_info() if self._transformers_manager else {},
                "available": self._transformers_manager.is_model_loaded() if self._transformers_manager else False
            }
        else:
            return {"backend": None, "available": False}
    
    def load_model(self) -> bool:
        """Load the model for the active backend."""
        if not self.is_available():
            logger.error("No backend available for model loading")
            return False
        
        if self._active_backend == "ollama":
            # Ollama models are loaded on-demand
            return self._ollama_manager.ensure_model(self.settings.offline_llm_model)
        elif self._active_backend == "transformers":
            return self._transformers_manager.load_model()
        
        return False
    
    def is_model_loaded(self) -> bool:
        """Check if model is loaded."""
        if not self.is_available():
            return False
        
        if self._active_backend == "ollama":
            models = self._ollama_manager.client.list_models()
            model_names = [m.get("name", "") for m in models]
            return self.settings.offline_llm_model in model_names
        elif self._active_backend == "transformers":
            return self._transformers_manager.is_model_loaded()
        
        return False
    
    def generate_response(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """Generate response using the active backend."""
        if not self.is_available():
            return "Error: No offline LLM backend available"
        
        temperature = temperature or self.settings.temperature
        max_tokens = max_tokens or self.settings.max_tokens
        
        if self._active_backend == "ollama":
            return self._ollama_manager.generate_response(
                prompt=prompt,
                model=self.settings.offline_llm_model,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
        elif self._active_backend == "transformers":
            return self._transformers_manager.generate_response(
                prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
        
        return "Error: No active backend for generation"
    
    def generate_educational_response(
        self,
        question: str,
        context: str = "",
        user_type: str = "teacher",
        max_length: int = 1024
    ) -> str:
        """Generate educational response with context."""
        if user_type == "teacher":
            system_prompt = "You are an expert educational assistant helping teachers create engaging learning content."
        else:
            system_prompt = "You are a helpful educational assistant for students."
        
        prompt = f"{system_prompt}\n\nContext: {context}\n\nQuestion: {question}\n\nAnswer:"
        
        return self.generate_response(
            prompt=prompt,
            max_tokens=max_length
        )
    
    def generate_curriculum_content(
        self,
        topic: str,
        level: str = "intermediate",
        duration: str = "1 hour",
        objectives: list = None
    ) -> dict:
        """Generate curriculum content."""
        objectives_str = ", ".join(objectives) if objectives else "general understanding"
        
        prompt = f"""Create a curriculum for the topic: {topic}
Level: {level}
Duration: {duration}
Learning Objectives: {objectives_str}

Please provide a structured curriculum with:
1. Learning objectives
2. Key concepts
3. Activities
4. Assessment methods
"""
        
        content = self.generate_response(prompt=prompt)
        
        return {
            "topic": topic,
            "level": level,
            "duration": duration,
            "objectives": objectives,
            "content": content
        }


# Global instance
_unified_service = None


def get_unified_llm_service() -> UnifiedOfflineLLMService:
    """Get the global unified LLM service instance."""
    global _unified_service
    if _unified_service is None:
        _unified_service = UnifiedOfflineLLMService()
    return _unified_service
