FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Ollama
RUN curl -fsSL https://ollama.ai/install.sh | sh

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data uploads outputs temp audio

# Set environment variables
ENV PYTHONPATH=/app/src
ENV OFFLINE_LLM_ENABLED=true
ENV OFFLINE_LLM_PROVIDER=ollama
ENV OFFLINE_LLM_MODEL=gpt-oss:20b
ENV OLLAMA_BASE_URL=http://localhost:11434
ENV API_HOST=0.0.0.0
ENV API_PORT=8000
ENV DEBUG=false
ENV DATABASE_URL=sqlite+aiosqlite:///./data/learnlocal.db

# Model configuration for dynamic switching
ENV OLLAMA_MODELS="llama3:8b,gpt-oss:20b"

# Expose ports
EXPOSE 8000 11434

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Start script
COPY docker-entrypoint.sh /
RUN chmod +x /docker-entrypoint.sh

ENTRYPOINT ["/docker-entrypoint.sh"]