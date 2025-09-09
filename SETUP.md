# LearnerExpert Setup Guide

## Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/Animesh-Uttekar/learnerexpert.git
   cd learnerexpert
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Download the AI model** (One-time setup)
   ```bash
   python setup_model.py
   ```
   
   This will download the OpenAI GPT-OSS-20B model (~13.8GB). It may take 10-20 minutes.

5. **Start the server**
   ```bash
   ./manage_server.sh start
   ```

6. **Access the application**
   - Server: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - React Frontend: Start the web app in `learnerexpert-web/`

## Requirements

- **Python**: 3.9 or higher
- **Memory**: 16GB RAM recommended for the AI model
- **Storage**: 15GB free space for model download
- **Internet**: Required for initial model download

## Troubleshooting

### Model Download Issues
- Ensure stable internet connection
- Check available disk space (need ~15GB)
- If download fails, run `python setup_model.py` again

### Server Issues
- Make sure port 8000 is available
- Check that virtual environment is activated
- Verify all dependencies are installed

### Performance
- First AI request may take 2-3 minutes (model loading)
- Subsequent requests are much faster
- Consider using GPU for better performance

## Features

- **Offline AI Assistant**: Educational Q&A using GPT-OSS-20B
- **Text-to-Speech**: Convert responses to audio
- **Multi-Agent System**: LangGraph workflow orchestration
- **Analytics**: Track usage and performance
- **Web Interface**: Modern React TypeScript frontend

## Testing

Run the comprehensive test suite:

```bash
./manage_server.sh test
```

Or test individual components:
```bash
python test_learnerexpert.py quick      # Quick tests
python test_learnerexpert.py standard   # Standard performance tests
python test_learnerexpert.py educational # Educational content tests
```

## Server Management

Use the unified server management script:

```bash
./manage_server.sh start    # Start server
./manage_server.sh stop     # Stop server  
./manage_server.sh restart  # Restart server
./manage_server.sh status   # Check status
./manage_server.sh test     # Run full test suite
```

## Development

To contribute or modify the system:

1. Follow setup steps above
2. Make changes to the code
3. Test with `./manage_server.sh test`
4. Submit pull requests

For detailed API documentation, visit http://localhost:8000/docs when the server is running.