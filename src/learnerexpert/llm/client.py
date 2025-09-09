"""
OpenAI client wrapper for LearnerExpert.

Provides a unified interface for OpenAI API calls with error handling,
caching, and configuration management.
"""

import json
import logging
from functools import lru_cache
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta

from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langchain_core.tools import BaseTool

from learnerexpert.config.settings import get_settings

logger = logging.getLogger(__name__)

_response_cache: Dict[str, Dict[str, Any]] = {}


class OpenAIClientWrapper:
    """Wrapper for OpenAI client with caching and error handling."""
    
    def __init__(self, model: str = None, temperature: float = None):
        self.settings = get_settings()
        self.model = model or self.settings.openai_model
        self.temperature = temperature or self.settings.temperature
        
        self._client = ChatOpenAI(
            api_key=self.settings.openai_api_key,
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.settings.max_tokens,
            timeout=30.0,
        )
        
        logger.info(f"Initialized OpenAI client with model: {self.model}")
    
    def _generate_cache_key(self, messages: List[BaseMessage], **kwargs) -> str:
        """Generate cache key for request."""
        content = str([msg.content for msg in messages])
        params = str(sorted(kwargs.items()))
        return f"{self.model}:{hash(content + params)}"
    
    def _is_cache_valid(self, cache_entry: Dict[str, Any]) -> bool:
        """Check if cache entry is still valid."""
        if not self.settings.cache_llm_responses:
            return False
        
        cached_time = datetime.fromisoformat(cache_entry["timestamp"])
        expiry_time = cached_time + timedelta(seconds=self.settings.cache_duration)
        
        return datetime.now() < expiry_time
    
    def _cache_response(self, cache_key: str, response: Any) -> None:
        """Cache response if caching is enabled."""
        if self.settings.cache_llm_responses:
            _response_cache[cache_key] = {
                "response": response,
                "timestamp": datetime.now().isoformat(),
                "model": self.model
            }
    
    async def ainvoke(
        self, 
        messages: List[BaseMessage], 
        tools: List[BaseTool] = None,
        **kwargs
    ) -> AIMessage:
        """Async invoke with caching and error handling."""
        
        cache_key = self._generate_cache_key(messages, **kwargs)
        if cache_key in _response_cache:
            cache_entry = _response_cache[cache_key]
            if self._is_cache_valid(cache_entry):
                logger.debug(f"Cache hit for key: {cache_key[:16]}...")
                return cache_entry["response"]
            else:
                del _response_cache[cache_key]
        
        try:
            if self.settings.mock_llm_responses:
                return self._get_mock_response(messages)
            
            client = self._client
            if tools:
                client = self._client.bind_tools(tools)
            
            logger.debug(f"Making OpenAI API call with {len(messages)} messages")
            response = await client.ainvoke(messages, **kwargs)
            
            self._cache_response(cache_key, response)
            
            logger.debug(f"OpenAI API call successful: {len(str(response.content))} chars")
            return response
            
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            return AIMessage(
                content=f"I apologize, but I'm experiencing technical difficulties. "
                       f"Error: {str(e)[:100]}..."
            )
    
    def invoke(
        self, 
        messages: List[BaseMessage], 
        tools: List[BaseTool] = None,
        **kwargs
    ) -> AIMessage:
        """Synchronous invoke (wrapper for async)."""
        import asyncio
        return asyncio.run(self.ainvoke(messages, tools, **kwargs))
    
    def _get_mock_response(self, messages: List[BaseMessage]) -> AIMessage:
        """Generate mock response for testing."""
        last_message = messages[-1] if messages else None
        
        if not last_message:
            return AIMessage(content="Mock response: No input provided.")
        
        content = last_message.content.lower()
        
        if "curriculum" in content and "validate" in content:
            mock_content = """
            Based on my analysis of the curriculum:
            
            **Gaps Identified:**
            - Missing Ethics in AI module
            - Limited coverage of RAG (Retrieval-Augmented Generation)
            - No practical implementation projects
            
            **Alignment Score:** 7.5/10 with provided OKRs
            
            **Recommendations:**
            1. Add 2-week Ethics module in Week 3
            2. Expand RAG coverage in Week 6
            3. Include capstone project in final weeks
            """
        
        elif "quiz" in content or "question" in content:
            mock_content = """
            Here are 5 sample quiz questions:
            
            1. **Multiple Choice:** What is the primary advantage of RAG systems?
               A) Reduced computational cost
               B) Access to updated information
               C) Simplified architecture
               D) Faster inference
               
            2. **True/False:** Transformer models can only process sequential data.
            
            3. **Short Answer:** Explain the ethical implications of AI bias in hiring systems.
            
            4. **Multiple Choice:** Which technique helps prevent overfitting?
               A) Dropout
               B) Batch normalization
               C) Data augmentation
               D) All of the above
               
            5. **Essay:** Describe how you would implement a RAG system for a company knowledge base.
            """
        
        elif "enrich" in content or "content" in content:
            mock_content = """
            **Enrichment Suggestions:**
            
            **Case Studies:**
            1. Netflix Recommendation System - ML in production
            2. ChatGPT Development - Large language model training
            
            **Hands-on Labs:**
            1. Build a simple RAG system using OpenAI API
            2. Implement bias detection in ML models
            
            **Additional Resources:**
            - "Attention Is All You Need" paper (Transformers)
            - Andrew Ng's ML Course (Coursera)
            - Fast.ai practical deep learning course
            """
        
        else:
            mock_content = f"Mock response for: {content[:50]}..."
        
        return AIMessage(content=mock_content)
    
    def get_embedding(self, text: str) -> List[float]:
        """Get embedding for text (placeholder for future implementation)."""
        return [0.0] * 1536
    
    def estimate_tokens(self, messages: List[BaseMessage]) -> int:
        """Estimate token count (rough approximation)."""
        total_chars = sum(len(str(msg.content)) for msg in messages)
        return total_chars // 4
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about current model."""
        return {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.settings.max_tokens,
            "cache_enabled": self.settings.cache_llm_responses,
            "mock_mode": self.settings.mock_llm_responses,
        }


@lru_cache()
def get_openai_client(model: str = None, temperature: float = None) -> OpenAIClientWrapper:
    """Get cached OpenAI client instance."""
    return OpenAIClientWrapper(model=model, temperature=temperature)


def get_openai_client_with_tools(tools: List[BaseTool]) -> ChatOpenAI:
    """Get OpenAI client with tools bound."""
    settings = get_settings()
    
    client = ChatOpenAI(
        api_key=settings.openai_api_key,
        model=settings.openai_model,
        temperature=settings.temperature,
        max_tokens=settings.max_tokens,
        timeout=30.0,
    )
    
    return client.bind_tools(tools)


def clear_cache():
    """Clear the response cache."""
    global _response_cache
    _response_cache.clear()
    logger.info("OpenAI response cache cleared")


def get_cache_stats() -> Dict[str, int]:
    """Get cache statistics."""
    return {
        "total_entries": len(_response_cache),
        "valid_entries": sum(
            1 for entry in _response_cache.values()
            if get_openai_client()._is_cache_valid(entry)
        )
    }