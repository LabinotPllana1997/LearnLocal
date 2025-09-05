"""
Configuration settings for LearnerExpert using Pydantic Settings.

Manages environment variables and application configuration with validation.
"""

import os
from functools import lru_cache
from typing import List, Optional, Dict, Any
from pydantic import Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # OpenAI Configuration
    openai_api_key: str = Field(..., description="OpenAI API key")
    openai_model: str = Field(default="gpt-4o-mini", description="Default OpenAI model")
    openai_embedding_model: str = Field(
        default="text-embedding-3-small", 
        description="OpenAI embedding model"
    )
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="LLM temperature")
    max_tokens: int = Field(default=2000, ge=1, le=4096, description="Max tokens per request")
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, ge=1, le=65535, description="API port")
    debug: bool = Field(default=True, description="Debug mode")
    log_level: str = Field(default="DEBUG", description="Logging level")
    
    # LangGraph Configuration
    langgraph_checkpoint_type: str = Field(default="memory", description="Checkpoint type")
    langgraph_checkpoint_path: str = Field(
        default="./data/checkpoints", 
        description="Checkpoint storage path"
    )
    langgraph_debug: bool = Field(default=True, description="LangGraph debug mode")
    
    # Memory Configuration
    memory_type: str = Field(default="file", description="Memory storage type")
    memory_path: str = Field(default="./data/memory", description="Memory storage path")
    memory_search_limit: int = Field(default=5, ge=1, description="Memory search result limit")
    
    # UI Configuration
    ui_enabled: bool = Field(default=True, description="Enable Streamlit UI")
    ui_port: int = Field(default=8501, ge=1, le=65535, description="UI port")
    ui_host: str = Field(default="0.0.0.0", description="UI host")
    
    # File Processing Configuration
    max_file_size: int = Field(default=10485760, description="Max file size (10MB)")
    allowed_extensions: List[str] = Field(
        default=["pdf", "docx", "txt", "pptx"],
        description="Allowed file extensions"
    )
    upload_directory: str = Field(default="./uploads", description="Upload directory")
    
    # Output Configuration
    output_directory: str = Field(default="./outputs", description="Output directory")
    export_formats: List[str] = Field(
        default=["csv", "json", "html", "pdf"],
        description="Available export formats"
    )
    
    # Voice Processing
    whisper_model: str = Field(default="base", description="Whisper model size")
    enable_voice_input: bool = Field(default=False, description="Enable voice processing")
    
    # Workflow Configuration
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
    
    # Company/OKR Configuration
    default_company_okrs: str = Field(
        default="Improve AI/ML skills,Enhance data literacy,Build technical leadership,Foster innovation culture",
        description="Default company OKRs"
    )
    default_industry: str = Field(default="Technology", description="Default industry")
    
    # Development/Testing
    mock_llm_responses: bool = Field(default=False, description="Use mock LLM responses")
    cache_llm_responses: bool = Field(default=True, description="Cache LLM responses")
    cache_duration: int = Field(default=3600, ge=0, description="Cache duration (seconds)")
    
    @validator("allowed_extensions", pre=True)
    def parse_extensions(cls, v):
        """Parse comma-separated extensions string."""
        if isinstance(v, str):
            return [ext.strip().lower() for ext in v.split(",")]
        return v
    
    @validator("export_formats", pre=True)
    def parse_formats(cls, v):
        """Parse comma-separated formats string."""
        if isinstance(v, str):
            return [fmt.strip().lower() for fmt in v.split(",")]
        return v
    
    @validator("default_company_okrs", pre=True)
    def parse_okrs(cls, v):
        """Parse comma-separated OKRs string."""
        if isinstance(v, str):
            return v  # Keep as string, will be split when used
        return v
    
    def get_okrs_list(self) -> List[str]:
        """Get OKRs as a list."""
        return [okr.strip() for okr in self.default_company_okrs.split(",")]
    
    def ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        directories = [
            self.upload_directory,
            self.output_directory,
            self.memory_path,
            os.path.dirname(self.langgraph_checkpoint_path)
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    def get_openai_config(self) -> Dict[str, Any]:
        """Get OpenAI configuration dict."""
        return {
            "api_key": self.openai_api_key,
            "model": self.openai_model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
    
    def get_langgraph_config(self) -> Dict[str, Any]:
        """Get LangGraph configuration dict."""
        return {
            "checkpoint_type": self.langgraph_checkpoint_type,
            "checkpoint_path": self.langgraph_checkpoint_path,
            "debug": self.langgraph_debug,
        }
    
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.debug and self.log_level.upper() in ["DEBUG", "DEV"]
    
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return not self.debug and self.log_level.upper() in ["INFO", "WARNING", "ERROR"]


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


def validate_environment() -> bool:
    """Validate that all required environment variables are set."""
    try:
        settings = get_settings()
        
        # Check critical settings
        required_checks = [
            (settings.openai_api_key, "OpenAI API key not set"),
            (settings.openai_api_key.startswith("sk-"), "Invalid OpenAI API key format"),
        ]
        
        for check, error_msg in required_checks:
            if not check:
                print(f"❌ {error_msg}")
                return False
        
        # Ensure directories exist
        settings.ensure_directories()
        
        print("✅ Environment validation passed")
        return True
        
    except Exception as e:
        print(f"❌ Environment validation failed: {e}")
        return False


def print_config_summary():
    """Print a summary of current configuration."""
    settings = get_settings()
    
    print("🔧 LearnerExpert Configuration Summary")
    print("=" * 40)
    print(f"OpenAI Model: {settings.openai_model}")
    print(f"API Port: {settings.api_port}")
    print(f"Debug Mode: {settings.debug}")
    print(f"Memory Type: {settings.memory_type}")
    print(f"UI Enabled: {settings.ui_enabled}")
    print(f"Voice Input: {settings.enable_voice_input}")
    print(f"Default Industry: {settings.default_industry}")
    print(f"Cache Enabled: {settings.cache_llm_responses}")
    print("=" * 40)


if __name__ == "__main__":
    # Quick configuration test
    if validate_environment():
        print_config_summary()
    else:
        print("Configuration validation failed!")