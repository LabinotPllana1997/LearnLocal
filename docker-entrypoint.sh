#!/bin/bash
set -e

echo "Starting LearnerExpert with Dynamic Model Support..."

# Start Ollama service in background
echo "Starting Ollama service..."
ollama serve &
OLLAMA_PID=$!

# Wait for Ollama to be ready
echo "Waiting for Ollama to start..."
sleep 10

# Pull both models for dynamic switching
echo "Checking for Ollama models..."
MODELS=(${OLLAMA_MODELS//,/ })

for model in "${MODELS[@]}"; do
    if ! ollama list | grep -q "$model"; then
        echo "Downloading $model model (this may take a while)..."
        if [[ "$model" == "llama3:8b" ]]; then
            echo "Model size: ~4.7GB"
        elif [[ "$model" == "gpt-oss:20b" ]]; then
            echo "Model size: ~13GB"
        fi
        ollama pull "$model"
    else
        echo "Model $model already available"
    fi
done

echo "Available models for dynamic switching:"
ollama list

# Function to handle shutdown
cleanup() {
    echo "Shutting down services..."
    kill $OLLAMA_PID 2>/dev/null || true
    exit 0
}

# Set up signal handlers
trap cleanup SIGTERM SIGINT

# Start the LearnerExpert application
echo "Starting LearnerExpert API server..."
cd /app
python main.py &
APP_PID=$!

# Wait for either process to exit
wait $APP_PID