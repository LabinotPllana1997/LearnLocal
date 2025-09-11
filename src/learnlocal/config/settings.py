"""
Configuration settings for LearnerExpert using Pydantic Settings.

Manages environment variables and application configuration with validation.
"""

import os
import logging
from functools import lru_cache
from typing import List, Optional, Dict, Any
from pydantic import Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    openai_api_key: str = Field(default="", description="OpenAI API key")
    openai_model: str = Field(default="gpt-4o-mini", description="Default OpenAI model")
    openai_embedding_model: str = Field(
        default="text-embedding-3-small", 
        description="OpenAI embedding model"
    )
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="LLM temperature")
    max_tokens: int = Field(default=2000, ge=1, le=4096, description="Max tokens per request")
    
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, ge=1, le=65535, description="API port")
    debug: bool = Field(default=True, description="Debug mode")
    log_level: str = Field(default="DEBUG", description="Logging level")
    
    langgraph_checkpoint_type: str = Field(default="memory", description="Checkpoint type")
    langgraph_checkpoint_path: str = Field(
        default="./data/checkpoints", 
        description="Checkpoint storage path"
    )
    langgraph_debug: bool = Field(default=True, description="LangGraph debug mode")
    
    memory_type: str = Field(default="file", description="Memory storage type")
    memory_path: str = Field(default="./data/memory", description="Memory storage path")
    memory_search_limit: int = Field(default=5, ge=1, description="Memory search result limit")
    
    ui_enabled: bool = Field(default=True, description="Enable Streamlit UI")
    ui_port: int = Field(default=8501, ge=1, le=65535, description="UI port")
    ui_host: str = Field(default="0.0.0.0", description="UI host")
    
    max_file_size: int = Field(default=10485760, description="Max file size (10MB)")
    allowed_extensions: List[str] = Field(
        default=["pdf", "docx", "txt", "pptx"],
        description="Allowed file extensions"
    )
    upload_directory: str = Field(default="./uploads", description="Upload directory")
    
    output_directory: str = Field(default="./outputs", description="Output directory")
    export_formats: List[str] = Field(
        default=["csv", "json", "html", "pdf"],
        description="Available export formats"
    )
    
    whisper_model: str = Field(default="base", description="Whisper model size")
    enable_voice_input: bool = Field(default=False, description="Enable voice processing")
    
    default_workflow_timeout: int = Field(
        default=300, 
        ge=30, 
        description="Default workflow timeout (seconds)"
    )
    max_agent_retries: int = Field(default=3, ge=1, description="Max agent retry attempts")
    enable_parallel_processing: bool = Field(
        default=False, 
        description="Enable parallel agent execution"
    )
    
    default_company_okrs: str = Field(
        default="Improve AI/ML skills,Enhance data literacy,Build technical leadership,Foster innovation culture",
        description="Default company OKRs"
    )
    default_industry: str = Field(default="Technology", description="Default industry")
    
    mock_llm_responses: bool = Field(default=False, description="Use mock LLM responses")
    cache_llm_responses: bool = Field(default=True, description="Cache LLM responses")
    cache_duration: int = Field(default=3600, ge=0, description="Cache duration (seconds)")
    
    offline_llm_enabled: bool = Field(default=True, description="Enable offline LLM")
    offline_llm_provider: str = Field(default="ollama", description="Offline LLM provider (ollama or transformers)")
    offline_llm_model: str = Field(
        default="llama3.1:8b",
        description="Offline LLM model name"
    )
    offline_llm_device: str = Field(default="auto", description="Device for offline LLM")
    
    use_quantization: bool = Field(default=False, description="Enable model quantization for speed")
    quantization_bits: int = Field(default=8, description="Quantization bits (4 or 8)")
    use_torch_compile: bool = Field(default=False, description="Use PyTorch 2.0 compilation")
    max_memory_gb: int = Field(default=8, description="Maximum memory usage in GB")
    enable_kv_cache: bool = Field(default=True, description="Enable key-value caching")
    
    ollama_base_url: str = Field(default="http://localhost:11434", description="Ollama server URL")
    ollama_timeout: int = Field(default=60, description="Ollama request timeout")
    ollama_auto_pull: bool = Field(default=True, description="Auto-pull models if not available")
    
    frontend_origins: List[str] = Field(
        default=[
            "http://localhost:3000", 
            "http://127.0.0.1:3000",
            "https://learnlocal-expo-app-y538.bolt.host",
            "*"
        ],
        description="Allowed frontend origins for CORS"
    )
    api_base_url: str = Field(default="http://localhost:8000", description="API base URL")
    docs_url: str = Field(default="/docs", description="API documentation URL path")
    health_url: str = Field(default="/health", description="Health check URL path")
    
    tts_enabled: bool = Field(default=True, description="Enable text-to-speech")
    tts_default_engine: str = Field(default="pyttsx3", description="Default TTS engine")
    tts_speed: float = Field(default=1.0, ge=0.1, le=3.0, description="TTS speed")
    tts_cleanup_hours: int = Field(default=24, ge=1, description="TTS cleanup hours")
    
    database_url: str = Field(
        default="sqlite+aiosqlite:///./data/learnlocal.db",
        description="Database URL"
    )
    database_echo: bool = Field(default=False, description="Database echo SQL")
    
    @validator("allowed_extensions", pre=True)
    def parse_extensions(cls, v):
        if isinstance(v, str):
            return [ext.strip().lower() for ext in v.split(",")]
        return v
    
    @validator("export_formats", pre=True)
    def parse_formats(cls, v):
        if isinstance(v, str):
            return [fmt.strip().lower() for fmt in v.split(",")]
        return v
    
    @validator("default_company_okrs", pre=True)
    def parse_okrs(cls, v):
        if isinstance(v, str):
            return v  # Keep as string, will be split when used
        return v
    
    def get_okrs_list(self) -> List[str]:
        return [okr.strip() for okr in self.default_company_okrs.split(",")]
    
    def ensure_directories(self) -> None:
        directories = [
            self.upload_directory,
            self.output_directory,
            self.memory_path,
            os.path.dirname(self.langgraph_checkpoint_path)
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    def get_openai_config(self) -> Dict[str, Any]:
        return {
            "api_key": self.openai_api_key,
            "model": self.openai_model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
    
    def get_langgraph_config(self) -> Dict[str, Any]:
        return {
            "checkpoint_type": self.langgraph_checkpoint_type,
            "checkpoint_path": self.langgraph_checkpoint_path,
            "debug": self.langgraph_debug,
        }
    
    def is_development(self) -> bool:
        return self.debug and self.log_level.upper() in ["DEBUG", "DEV"]
    
    def is_production(self) -> bool:
        return not self.debug and self.log_level.upper() in ["INFO", "WARNING", "ERROR"]


@lru_cache()
def get_settings() -> Settings:
    return Settings()


def validate_environment() -> bool:
    try:
        settings = get_settings()
        
        # Check critical settings
        required_checks = [
            (settings.openai_api_key, "OpenAI API key not set"),
            (settings.openai_api_key.startswith("sk-"), "Invalid OpenAI API key format"),
        ]
        
        for check, error_msg in required_checks:
            if not check:
                logger.error(error_msg)
                return False
        
        # Ensure directories exist
        settings.ensure_directories()
        
        logger.info("Environment validation passed")
        return True
        
    except Exception as e:
        logger.error(f"Environment validation failed: {e}")
        return False


def print_config_summary():
    settings = get_settings()
    
    logger.info("LearnerExpert Configuration Summary")
    logger.info(f"OpenAI Model: {settings.openai_model}")
    logger.info(f"API Port: {settings.api_port}")
    logger.info(f"Debug Mode: {settings.debug}")
    logger.info(f"Memory Type: {settings.memory_type}")
    logger.info(f"UI Enabled: {settings.ui_enabled}")
    logger.info(f"Voice Input: {settings.enable_voice_input}")
    logger.info(f"Default Industry: {settings.default_industry}")
    logger.info(f"Cache Enabled: {settings.cache_llm_responses}")


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    if validate_environment():
        print_config_summary()
    else:
        logger.error("Configuration validation failed!")