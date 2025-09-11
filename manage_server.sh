#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="$SCRIPT_DIR/venv/bin/python"
MAIN_SCRIPT="$SCRIPT_DIR/main.py"

# Get port from settings if available, fallback to 8000
if command -v python3 &> /dev/null; then
    PORT=$(python3 -c "
import sys
sys.path.insert(0, '$SCRIPT_DIR/src')
try:
    from learnlocal.config.settings import get_settings
    settings = get_settings()
    print(settings.api_port)
except:
    print(8000)
" 2>/dev/null)
else
    PORT=8000
fi

show_usage() {
    echo "Usage: ./manage_server.sh [setup|start|stop|restart|status|test]"
    echo ""
    echo "Commands:"
    echo "  setup    - Run initial setup (install dependencies and Ollama)"
    echo "  start    - Start the LearnerExpert server"
    echo "  stop     - Stop the server and cleanup processes"
    echo "  restart  - Stop and start the server"
    echo "  status   - Check server status"
    echo "  test     - Run full test suite"
    echo ""
}

check_server_status() {
    if curl -s "http://localhost:$PORT/health" > /dev/null 2>&1; then
        echo "Server is running on http://localhost:$PORT"
        return 0
    else
        echo "Server is not running"
        return 1
    fi
}

cleanup_processes() {
    echo "Cleaning up existing processes..."
    
    lsof -ti:$PORT | xargs kill -9 2>/dev/null || true
    
    ps aux | grep "python.*main.py" | grep -v grep | awk '{print $2}' | xargs kill -9 2>/dev/null || true
    
    sleep 2
    echo "Cleanup completed"
}

check_dependencies() {
    echo "Checking dependencies..."
    
    # Try to import key dependencies
    if [[ -f "$VENV_PATH" ]]; then
        "$VENV_PATH" -c "import fastapi, uvicorn, aiosqlite" 2>/dev/null
    else
        python3 -c "import fastapi, uvicorn, aiosqlite" 2>/dev/null
    fi
    
    if [ $? -ne 0 ]; then
        echo "ERROR: Dependencies not installed!"
        echo ""
        echo "Please install dependencies first:"
        echo "  1. Activate virtual environment: source venv/bin/activate"
        echo "  2. Install dependencies: pip install -r requirements.txt"
        echo ""
        echo "Or run setup:"
        echo "  python -m venv venv"
        echo "  source venv/bin/activate" 
        echo "  pip install -r requirements.txt"
        return 1
    fi
    return 0
}

start_server() {
    echo "Starting LearnerExpert Server..."
    
    if check_server_status > /dev/null 2>&1; then
        echo "Server is already running"
        return 0
    fi
    
    # Check dependencies first
    if ! check_dependencies; then
        return 1
    fi
    
    cleanup_processes
    
    # Determine Python command to use
    if [[ -f "$VENV_PATH" ]]; then
        PYTHON_CMD="$VENV_PATH"
        echo "Using virtual environment: $VENV_PATH"
    elif command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
        echo "Using system python3"
    else
        echo "Error: No Python interpreter found"
        return 1
    fi
    
    echo "Starting server on http://localhost:$PORT"
    echo "API Documentation: http://localhost:$PORT/docs"
    echo "Note: Background services will initialize after startup"
    echo "--------------------------------------------------------------"
    
    cd "$SCRIPT_DIR"
    
    # Start server with proper error handling
    if [[ -f "$VENV_PATH" ]]; then
        nohup "$VENV_PATH" "$MAIN_SCRIPT" > server.log 2>&1 &
    else
        nohup python3 "$MAIN_SCRIPT" > server.log 2>&1 &
    fi
    
    SERVER_PID=$!
    echo "Server starting... (PID: $SERVER_PID)"
    echo "Waiting for server to initialize..."
    
    # Wait for server to start with better error reporting
    for i in {1..30}; do
        if check_server_status > /dev/null 2>&1; then
            echo "Server started successfully"
            return 0
        fi
        
        # Check if process is still running
        if ! kill -0 $SERVER_PID 2>/dev/null; then
            echo ""
            echo "Server process died. Check server.log for errors:"
            tail -10 server.log
            return 1
        fi
        
        sleep 2
        echo -n "."
    done
    
    echo ""
    echo "Server may still be starting. Check server.log for details:"
    tail -5 server.log
}

stop_server() {
    echo "Stopping LearnerExpert Server..."
    cleanup_processes
    echo "Server stopped"
}

restart_server() {
    stop_server
    sleep 3
    start_server
}

run_tests() {
    echo "Running LearnerExpert Test Suite..."
    
    if ! check_server_status > /dev/null 2>&1; then
        echo "Server is not running. Starting server first..."
        start_server
        
        echo "Waiting for model to load (90 seconds)..."
        sleep 90
    fi
    
    cd "$SCRIPT_DIR"
    if [[ -f "$VENV_PATH" ]]; then
        $VENV_PATH test_learnlocal.py
    else
        python3 test_learnlocal.py
    fi
}

run_setup() {
    echo "LearnerExpert Setup Script"
    echo "========================="
    echo ""

    # Check if virtual environment exists
    if [[ ! -d "venv" ]]; then
        echo "Creating virtual environment..."
        python3 -m venv venv
        if [[ $? -ne 0 ]]; then
            echo "ERROR: Failed to create virtual environment"
            echo "Make sure python3 is installed"
            return 1
        fi
    fi

    # Activate virtual environment
    echo "Activating virtual environment..."
    source venv/bin/activate

    # Upgrade pip
    echo "Upgrading pip..."
    pip install --upgrade pip

    # Install dependencies
    echo "Installing Python dependencies..."
    pip install -r requirements.txt

    if [[ $? -ne 0 ]]; then
        echo "ERROR: Failed to install dependencies"
        echo "Check requirements.txt and try again"
        return 1
    fi

    # Install Ollama if not already installed
    echo ""
    echo "Checking Ollama installation..."
    if ! command -v ollama &> /dev/null; then
        echo "Ollama not found. Installing Ollama..."
        
        # Check if Homebrew is available
        if command -v brew &> /dev/null; then
            echo "Installing Ollama via Homebrew..."
            brew install ollama
            
            # Start Ollama service
            echo "Starting Ollama service..."
            brew services start ollama
            
            # Wait a moment for service to start
            sleep 3
        else
            echo "ERROR: Homebrew not found. Please install Ollama manually:"
            echo "  Visit: https://ollama.ai/download"
            echo "  Or install Homebrew first: https://brew.sh"
            return 1
        fi
    else
        echo "Ollama is already installed"
        
        # Ensure Ollama service is running
        if ! pgrep -f "ollama" > /dev/null; then
            echo "Starting Ollama service..."
            if command -v brew &> /dev/null; then
                brew services start ollama
            else
                echo "Please start Ollama manually: ollama serve"
            fi
            sleep 3
        fi
    fi

    # Pull the GPT-OSS-20B model
    echo ""
    echo "Downloading GPT-OSS-20B model (this may take several minutes)..."
    echo "Model size: ~13GB"
    # ollama pull gpt-oss:20b
    ollama pull llama3.1:8b


    if [[ $? -eq 0 ]]; then
        echo ""
        echo "✅ Setup completed successfully!"
        echo ""
        echo "🚀 To start the server:"
        echo "  ./manage_server.sh start"
        echo ""
        echo "📖 Or manually:"
        echo "  source venv/bin/activate"
        echo "  python main.py"
        echo ""
        echo "🧪 To run tests:"
        echo "  ./manage_server.sh test"
        echo ""
        echo "📊 Model info:"
        echo "  Model: GPT-OSS-20B via Ollama"
        echo "  Expected response time: 20-60 seconds"
        echo "  API: http://localhost:8000/docs"
        echo ""
    else
        echo "WARNING: Failed to download GPT-OSS-20B model"
        echo "You can download it later with: ollama pull gpt-oss:20b"
        echo ""
        echo "Setup completed with warnings."
    fi
}

case "${1:-}" in
    setup)
        run_setup
        ;;
    start)
        start_server
        ;;
    stop)
        stop_server
        ;;
    restart)
        restart_server
        ;;
    status)
        check_server_status
        ;;
    test)
        run_tests
        ;;
    *)
        show_usage
        exit 1
        ;;
esac