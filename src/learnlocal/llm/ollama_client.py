"""
Ollama client for offline LLM integration with FastAPI.
Provides OpenAI-compatible API interface for local model serving.
"""

import httpx
import json
import logging
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from ..config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class OllamaClient:
    """Client for interacting with local Ollama server."""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url.rstrip('/')
        self.client = httpx.Client(timeout=300.0)
    
    def is_available(self) -> bool:
        """Check if Ollama server is running."""
        try:
            response = self.client.get(f"{self.base_url}/api/tags")
            return response.status_code == 200
        except Exception as e:
            logger.debug(f"Ollama not available: {e}")
            return False
    
    def list_models(self) -> List[Dict[str, Any]]:
        """List available models in Ollama."""
        try:
            response = self.client.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                data = response.json()
                return data.get("models", [])
            return []
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return []
    
    def pull_model(self, model_name: str) -> bool:
        """Pull/download a model to Ollama."""
        try:
            response = self.client.post(
                f"{self.base_url}/api/pull",
                json={"name": model_name}
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Error pulling model {model_name}: {e}")
            return False
    
    def generate(
        self,
        model: str,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Optional[str]:
        """Generate text using Ollama model."""
        try:
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False
            }
            
            if temperature is not None:
                payload["options"] = payload.get("options", {})
                payload["options"]["temperature"] = temperature
            
            if max_tokens is not None:
                payload["options"] = payload.get("options", {})
                payload["options"]["num_predict"] = max_tokens
            
            response = self.client.post(
                f"{self.base_url}/api/generate",
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "")
            else:
                logger.error(f"Ollama generate failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error generating with Ollama: {e}")
            return None
    
    def chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Optional[str]:
        """Chat with Ollama model using messages format."""
        try:
            payload = {
                "model": model,
                "messages": messages,
                "stream": False
            }
            
            if temperature is not None:
                payload["options"] = payload.get("options", {})
                payload["options"]["temperature"] = temperature
            
            if max_tokens is not None:
                payload["options"] = payload.get("options", {})
                payload["options"]["num_predict"] = max_tokens
            
            response = self.client.post(
                f"{self.base_url}/api/chat",
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("message", {}).get("content", "")
            else:
                logger.error(f"Ollama chat failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error chatting with Ollama: {e}")
            return None
    
    def close(self):
        """Close the HTTP client."""
        self.client.close()


class OllamaManager:
    """Singleton manager for Ollama client."""
    
    _instance = None
    
    def __new__(cls, base_url: str = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.client = OllamaClient(base_url)
            cls._instance._initialized = True
        return cls._instance
    
    def __init__(self, base_url: str = None):
        if hasattr(self, '_initialized'):
            return
        self.client = OllamaClient(base_url)
        self._initialized = True
    
    def is_available(self) -> bool:
        """Check if Ollama is available."""
        return self.client.is_available()
    
    def ensure_model(self, model_name: str) -> bool:
        """Ensure model is available, pull if necessary."""
        models = self.client.list_models()
        model_names = [m.get("name", "") for m in models]
        
        if model_name in model_names:
            logger.info(f"Model {model_name} already available")
            return True
        
        logger.info(f"Pulling model {model_name}...")
        return self.client.pull_model(model_name)
    
    def generate_response(
        self,
        prompt: str,
        model: str = "llama3.1:8b",
        temperature: float = 0.7,
        max_tokens: int = 512,
        **kwargs
    ) -> str:
        """Generate response using Ollama."""
        if not self.client.is_available():
            return "Error: Ollama server not available"
        
        if not self.ensure_model(model):
            return f"Error: Could not load model {model}"
        
        response = self.client.generate(
            model=model,
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        
        if response is None:
            return "Error: Failed to generate response"
        
        return response.strip()


# Global instance
_ollama_manager = None


def get_ollama_manager(base_url: str = None) -> OllamaManager:
    """Get the global Ollama manager instance."""
    global _ollama_manager
    if _ollama_manager is None:
        _ollama_manager = OllamaManager(base_url)
    return _ollama_manager
