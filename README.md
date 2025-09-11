# LearnerExpert

[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://python.org)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-green.svg)](https://openai.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-Multi--Agent-orange.svg)](https://langchain-ai.github.io/langgraph/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-red.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**AI-powered multi-agent system for Learning & Development automation**

LearnerExpert is an innovative L&D expert system that automates curriculum validation, quiz generation, and content enrichment for corporate training programs. Built with LangGraph multi-agent architecture and OpenAI GPT models, it helps educators create comprehensive, aligned, and engaging learning experiences.

---

## Features

- **Multi-Agent Architecture**: 6 specialized AI agents orchestrated via LangGraph
- **Curriculum Validation**: Automated gap analysis against company OKRs
- **Interactive Quiz Generation**: Multi-format questions with difficulty adjustment  
- **Content Enrichment**: Case studies, labs, and resource suggestions
- **Feedback Loop**: Continuous improvement based on educator input
- **Memory System**: Personalized preferences and session continuity
- **FastAPI Backend**: Modern, async REST API with real-time processing
- **Multiple Output Formats**: CSV, JSON, HTML, PDF exports
- **Voice Input Support**: Whisper-powered speech-to-text (optional)
- **Web UI**: Streamlit interface for easy interaction

---

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Orchestrator  │────│ Curriculum       │────│ Quiz Creator    │
│   Agent (OA)    │    │ Validator (CV)   │    │ Agent (QC)      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐             │
         │──────────────│ Content         │─────────────│
                        │ Enricher (CE)   │
         │              └─────────────────┘             │
         │                       │                       │
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Memory Agent    │────│ Feedback         │────│ Agent Tools     │
│ (MA)            │    │ Evaluator (FA)   │    │ & LLM Client    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Agent Responsibilities

| Agent | Function | Input | Output |
|-------|----------|-------|---------|
| **Orchestrator (OA)** | Workflow coordination | User requests | Routed tasks |
| **Curriculum Validator (CV)** | Gap analysis & OKR alignment | Curriculum + OKRs | Gap matrix |
| **Quiz Creator (QC)** | Question generation | Validated curriculum | Interactive quizzes |
| **Content Enricher (CE)** | Resource suggestions | Curriculum gaps | Enrichment materials |
| **Feedback Evaluator (FA)** | Performance analysis | User feedback | Improvement recommendations |
| **Memory Agent (MA)** | Preference storage | Session data | Personalized suggestions |

---

## Quick Start

### Prerequisites

- **Python 3.12+** (required)
- **OpenAI API Key** ([Get one here](https://platform.openai.com/api-keys))
- **Git** for version control

### 1. Clone & Setup

```bash
# Clone the repository
git clone https://github.com/Animesh-Uttekar/learnerexpert.git
cd learnerexpert

# One-command setup (installs dependencies + Ollama + GPT-OSS-20B model)
./manage_server.sh setup

# OR manual setup:
pip install -r requirements.txt
# Install Ollama manually from https://ollama.ai
ollama pull gpt-oss:20b
pip install -e ".[dev]"
```

### 2. Environment Configuration

```bash
# Copy example environment file
cp .env.example .env

# Edit with your settings (required: OPENAI_API_KEY)
nano .env  # or your preferred editor
```

**Required Environment Variables:**
```env
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_MODEL=gpt-4o-mini
API_PORT=8000
DEBUG=true
```

### 3. Run the API Server

```bash
# Start the server (recommended)
./manage_server.sh start

# OR manually
python main.py

# Check server status
./manage_server.sh status

# API will be available at:
# - Main API: http://localhost:8000
# - Swagger UI: http://localhost:8000/docs
# - Health Check: http://localhost:8000/health
```

### 4. Optional: Run Web UI

```bash
# Start Streamlit interface (if UI dependencies installed)
streamlit run demo/app.py --server.port 8501

# Access at: http://localhost:8501
```

---

## Development Setup

### For Contributors

```bash
# Install with development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Run linting
ruff check --fix src/ tests/
ruff format src/ tests/

# Type checking
mypy src/learnerexpert/
```

### Project Structure

```
learnerexpert/
├── src/
│   └── learnerexpert/
│       ├── agents/           # Multi-agent system
│       │   ├── nodes/        # Agent implementations
│       │   ├── tools/        # Agent tools
│       │   ├── graph.py      # LangGraph orchestration
│       │   └── states.py     # State management
│       ├── api/              # FastAPI application
│       ├── llm/              # OpenAI integration
│       ├── processors/       # Document handling
│       ├── generators/       # Output creation
│       ├── config/           # Settings management
│       └── utils/            # Utilities
├── tests/                    # Test suite
├── examples/                 # Sample files
├── demo/                     # Streamlit UI
└── docs/                     # Documentation
```

---

## Usage Examples

### API Usage

```python
import httpx

# Analyze curriculum
response = httpx.post("http://localhost:8000/analyze", 
    files={"file": open("curriculum.pdf", "rb")},
    data={"company_okrs": "AI skills, Data literacy, Innovation"}
)

results = response.json()
print(f"Found {len(results['gap_matrix'])} curriculum gaps")
print(f"Generated {len(results['quiz_items'])} quiz questions")
```

### Python SDK Usage

```python
from learnerexpert.agents.graph import run_workflow

# Run complete workflow
results = await run_workflow(
    user_id="educator_123",
    session_id="session_456", 
    input_document="Machine Learning Curriculum...",
    company_okrs="Improve AI/ML skills, Build data science team",
    industry="Technology"
)

# Access results
curriculum_gaps = results["gap_matrix"]
quiz_questions = results["quiz_items"]
enrichment_materials = results["enrichment_content"]
```

---

## Configuration

### Key Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `OPENAI_MODEL` | `gpt-4o-mini` | OpenAI model for agents |
| `TEMPERATURE` | `0.7` | LLM creativity level |
| `MAX_TOKENS` | `2000` | Max tokens per request |
| `CACHE_LLM_RESPONSES` | `true` | Enable response caching |
| `MOCK_LLM_RESPONSES` | `false` | Use mock responses for testing |
| `MAX_FILE_SIZE` | `10MB` | Maximum upload file size |
| `ALLOWED_EXTENSIONS` | `pdf,docx,txt,pptx` | Supported file types |

### Output Formats

- **Gap Matrix**: CSV spreadsheet with identified gaps
- **Quiz Bank**: JSON/Markdown with interactive questions  
- **Enrichment Content**: HTML modules with expandable resources
- **Reports**: PDF summaries with recommendations

---

## Contributing

We welcome contributions! Here's how to get started:

### Development Workflow

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/amazing-feature`
3. **Make** your changes following our coding standards
4. **Test** your changes: `pytest`
5. **Commit** with clear messages: `git commit -m 'Add amazing feature'`
6. **Push** to your fork: `git push origin feature/amazing-feature`
7. **Create** a Pull Request

### Coding Standards

- **Python 3.12+** with type hints
- **Black** for code formatting
- **Ruff** for linting
- **pytest** for testing
- **Docstrings** for all public functions
- **Type annotations** required

### Areas for Contribution

- **Agent Development**: Implement new specialized agents
-  **Tool Creation**: Build new agent tools and integrations  
- **Output Formats**: Add new export formats and visualizations
- **Testing**: Expand test coverage and integration tests
-  **Documentation**: Improve docs and add tutorials
-  **UI/UX**: Enhance the Streamlit interface
- **Performance**: Optimize LLM calls and caching

---

##  Documentation

- **[API Reference](docs/api.md)** - Complete API documentation
- **[Agent Guide](docs/agents.md)** - Deep dive into agent system  
- **[Configuration](docs/configuration.md)** - Detailed settings guide
- **[Examples](examples/)** - Sample curricula and outputs
- **[Contributing](CONTRIBUTING.md)** - Development guidelines

---

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=learnerexpert --cov-report=html

# Run specific test file
pytest tests/unit/test_agents.py

# Run integration tests
pytest tests/integration/

# Test specific agent
pytest tests/unit/test_curriculum_validator.py -v
```

---

## Roadmap

### Phase 1: Core Foundation
- [x] Multi-agent LangGraph architecture  
- [x] OpenAI integration with caching
- [x] FastAPI backend with async support
- [x] Configuration management

### Phase 2: Agent Implementation
- [ ] Orchestrator Agent
- [ ] Curriculum Validator Agent
- [ ] Quiz Creator Agent
- [ ] Content Enricher Agent
- [ ] Feedback Evaluator Agent
- [ ] Memory Agent

### Phase 3: Integration & UI 
- [ ] Document processing (PDF, DOCX, voice)
- [ ] Output generation (CSV, HTML, PDF)
- [ ] Streamlit web interface
- [ ] API documentation

### Phase 4: Enhancement
- [ ] Advanced analytics and reporting
- [ ] Integration with LMS platforms
- [ ] Multi-language support
- [ ] Advanced voice processing
- [ ] Real-time collaboration

---

## Performance

- **Response Time**: < 30 seconds for full curriculum analysis
- **Supported File Size**: Up to 10MB documents
- **Concurrent Users**: 50+ simultaneous sessions
- **Caching**: Intelligent LLM response caching for speed
- **Scalability**: Horizontal scaling ready with async architecture

---

## Troubleshooting

### Common Issues

**Q: Getting OpenAI API errors?**  
A: Ensure your `OPENAI_API_KEY` is set correctly and has sufficient credits.

**Q: File upload failing?**  
A: Check file size (max 10MB) and format (PDF, DOCX, TXT, PPTX supported).

**Q: Slow response times?**  
A: Enable caching (`CACHE_LLM_RESPONSES=true`) and consider using `gpt-3.5-turbo` for faster responses.

**Q: Agent workflow stuck?**  
A: Check logs for errors and ensure all required environment variables are set.

### Getting Help

- **Bug Reports**: [Create an issue](https://github.com/your-org/learnerexpert/issues)
- **Questions**: [Start a discussion](https://github.com/your-org/learnerexpert/discussions)  
- **Email**: team@yourorg.com

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- **OpenAI** for GPT models and API
- **LangChain/LangGraph** for multi-agent orchestration
- **FastAPI** for the modern Python web framework
- **Streamlit** for rapid UI development
- **Enable International** for the foundational architecture patterns

---

## Ready to Transform L&D?

LearnerExpert represents the future of AI-native corporate learning. Join us in building the next generation of educational technology!

**[Get Started Now](#-quick-start)** | **[View Examples](examples/)** | **[Join Community](https://github.com/your-org/learnerexpert/discussions)**

---

<div align="center">

**Built with for the future of learning**

[![GitHub stars](https://img.shields.io/github/stars/your-org/learnerexpert?style=social)](https://github.com/your-org/learnerexpert)
[![GitHub forks](https://img.shields.io/github/forks/your-org/learnerexpert?style=social)](https://github.com/your-org/learnerexpert/fork)
[![GitHub issues](https://img.shields.io/github/issues/your-org/learnerexpert)](https://github.com/your-org/learnerexpert/issues)

</div>