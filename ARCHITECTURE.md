# LearnLocal Architecture Documentation

## System Overview

LearnLocal is an AI-powered educational platform built with a **multi-agent architecture** and **offline-first capabilities**. The system combines FastAPI for web services, LangGraph for multi-agent orchestration, and supports both offline (Ollama/Transformers) and online (OpenAI) LLM services.

## Architecture Layers

### 1. Application Layer
- **FastAPI Application** (`src/learnlocal/main.py`)
  - Primary web service entry point
  - CORS middleware for frontend integration
  - Application lifecycle management
  - Health check and root endpoints

### 2. API Layer  
- **Offline Endpoints** (`src/learnlocal/api/endpoints/offline_endpoints.py`)
  - Educational Q&A: `/api/ask`, `/api/chat`
  - Text-to-Speech: `/api/tts`
  - Content Generation: `/api/curriculum`, `/api/generate-lesson`
  - Analytics: `/api/history/questions`, `/api/analytics/summary`
  - System Monitoring: `/api/status`, `/api/health`

### 3. Multi-Agent System Layer
- **LangGraph Orchestration** (`src/learnlocal/agents/graph.py`)
  - **Orchestrator Agent**: Central coordination and routing
  - **Curriculum Validator**: Educational content validation
  - **Quiz Creator**: Assessment material generation
  - **Content Enricher**: Supplementary resource addition
  - **Feedback Evaluator**: User feedback analysis
  - **Memory Agent**: Session history and preferences

### 4. Service Layer
- **Unified LLM Service** (`src/learnlocal/services/unified_llm_service.py`)
  - Smart backend selection (Ollama → Transformers fallback)
  - Educational content generation with context awareness
  - Curriculum-specific response formatting

- **Text-to-Speech Service** (`src/learnlocal/services/tts_service.py`)
  - Multiple engine support (pyttsx3, Coqui TTS, Google TTS)
  - Asynchronous audio generation
  - File management and cleanup

- **Database Service** (`src/learnlocal/services/database_service.py`)
  - Question/answer persistence
  - Usage analytics and statistics
  - Audio generation tracking

### 5. LLM Integration Layer
- **Ollama Client** (`src/learnlocal/llm/ollama_client.py`)
  - Local model serving integration
  - OpenAI-compatible API interface
  - Model management (pull, list, availability)

- **Offline Model Manager** (`src/learnlocal/llm/offline_model_manager.py`)
  - Transformers-based model loading
  - Memory optimization and quantization
  - Device selection (CPU/CUDA/MPS)
  - GPT-OSS-20B model support

### 6. Data Layer
- **SQLite Database** (`src/learnlocal/database/`)
  - **Models**: Questions, AudioGeneration, UsageStats, SystemHealth
  - **Connection Management**: AsyncSession with pooling
  - **Schema Management**: SQLAlchemy declarative base

### 7. Configuration Layer
- **Pydantic Settings** (`src/learnlocal/config/settings.py`)
  - Environment variable management
  - Validation and type checking
  - Runtime configuration with defaults
  - Multi-environment support

## Technology Stack

### Core Frameworks
- **FastAPI**: Modern Python web framework
- **LangGraph**: Multi-agent workflow orchestration  
- **LangChain**: LLM integration and tool usage
- **Pydantic**: Data validation and settings
- **SQLAlchemy**: Async ORM with declarative models

### LLM and AI Stack
- **Transformers**: Hugging Face model loading
- **Ollama**: Local model serving platform
- **OpenAI**: Cloud LLM integration (fallback)
- **PyTorch**: Deep learning framework

### Additional Services
- **TTS Engines**: pyttsx3, Coqui TTS, Google TTS
- **Voice Processing**: OpenAI Whisper
- **HTTP Client**: httpx for async requests
- **Database**: SQLite with aiosqlite

## Data Flow

### Primary Request Flow
1. **Client Request** → FastAPI endpoint
2. **Request Processing** → Pydantic validation
3. **Service Selection** → Unified LLM Service backend selection
4. **LLM Processing** → Ollama or Transformers response generation
5. **Response Formatting** → Educational content formatting
6. **Database Logging** → Request/response tracking
7. **Response Return** → JSON response to client

### TTS Flow
1. **Text Input** → TTS request with preferences
2. **Engine Selection** → Best available TTS engine
3. **Audio Generation** → Async speech synthesis
4. **File Management** → Temporary file creation
5. **Response Delivery** → File download response

## Service Dependencies

### Internal Dependencies
- Unified LLM Service ← Ollama Client + Offline Model Manager
- Database Service ← SQLAlchemy Models + AsyncSession  
- API Endpoints ← All Services (LLM, TTS, Database)
- Multi-Agent System ← LangGraph + LangChain

### External Integrations
- **Ollama Server**: Local model serving (port 11434)
- **Hugging Face**: Model downloads and tokenizers
- **OpenAI API**: Fallback LLM service
- **File System**: Model caching and storage

## Performance Features

### Memory Management
- Model quantization (4-bit/8-bit) support
- Memory-mapped model loading
- CPU offloading for large models
- Automatic garbage collection

### Optimization
- LLM response caching with configurable TTL
- Model persistence between requests
- Key-value caching for inference  
- PyTorch compilation optimization

### Concurrency
- Full async/await support throughout
- Thread pool execution for blocking operations
- Async database operations
- Concurrent request handling

## Configuration Requirements

### Environment Variables
- `OPENAI_API_KEY`: Required for fallback LLM
- `OFFLINE_LLM_MODEL`: Model name (default: "llama3.1:8b")
- `OLLAMA_BASE_URL`: Ollama server endpoint  
- `DATABASE_URL`: SQLite database path
- Performance and optimization flags

### System Requirements
- **Memory**: 16GB+ RAM recommended for large models
- **Storage**: ~20GB for model caching
- **Network**: Optional for downloads and fallback services
- **Hardware**: CUDA/MPS support beneficial but not required

## Architecture Strengths

1. **Modularity**: Clear separation of concerns
2. **Flexibility**: Multiple LLM backend support
3. **Scalability**: Async architecture with efficient resources
4. **Offline-First**: Full functionality without internet
5. **Educational Focus**: Specialized content formatting
6. **Observability**: Comprehensive logging and analytics
7. **Type Safety**: Strong typing with Pydantic validation

## Development Setup

1. **Install Dependencies**: `pip install -r requirements.txt`
2. **Setup Ollama**: `brew install ollama && ollama pull llama3.1:8b`
3. **Configure Environment**: Copy `.env.example` to `.env`
4. **Initialize Database**: Automatic on first startup
5. **Start Server**: `./manage_server.sh start`

## API Documentation

- **Local API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/health
- **System Status**: http://localhost:8000/api/status

## Future Enhancements

- Full multi-agent workflow implementation
- Advanced curriculum validation algorithms
- Real-time collaboration features
- Enhanced analytics and reporting
- Mobile app integration
- Multi-language support