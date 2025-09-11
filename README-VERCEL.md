# Vercel Deployment Guide for LearnLocal

## Quick Deploy

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/Animesh-Uttekar/learnlocal)

## Environment Variables

Configure these environment variables in your Vercel dashboard:

### Required
```bash
OPENAI_API_KEY=your-openai-api-key
```

### Optional (with defaults)
```bash
# API Configuration
DEBUG=false
LOG_LEVEL=INFO
API_HOST=0.0.0.0
API_PORT=8000

# Feature Toggles (disabled for serverless)
OFFLINE_LLM_ENABLED=false
TTS_ENABLED=false

# Database (uses temporary SQLite)
DATABASE_URL=sqlite+aiosqlite:///tmp/learnlocal.db

# OpenAI Settings
OPENAI_MODEL=gpt-4o-mini
TEMPERATURE=0.7
MAX_TOKENS=2000
```

## Deployment Steps

1. **Fork/Clone Repository**
   ```bash
   git clone https://github.com/Animesh-Uttekar/learnlocal.git
   cd learnlocal
   ```

2. **Connect to Vercel**
   - Go to [vercel.com](https://vercel.com)
   - Import your GitHub repository
   - Configure environment variables

3. **Deploy**
   - Vercel will automatically deploy from `api/index.py`
   - API will be available at `https://your-app.vercel.app`

## API Endpoints

Once deployed, your API will be available at:

- Health Check: `GET /api/health`
- Chat: `POST /api/chat`
- Generate Lesson: `POST /api/generate-lesson`
- API Docs: `GET /docs` (in development mode)

## Limitations on Vercel

- **No Ollama/Offline LLM**: Serverless functions don't support long-running processes
- **No TTS**: File generation disabled for serverless
- **Temporary Database**: SQLite database resets on each function invocation
- **30s Timeout**: Functions timeout after 30 seconds

## Production Recommendations

For production use with full features (Ollama, TTS, persistent database):

1. **VPS/Cloud Server**: Deploy on AWS EC2, Google Cloud, or DigitalOcean
2. **Docker**: Use the provided Docker configuration
3. **Railway/Render**: Use platforms that support longer-running processes

## Local Testing

Test the Vercel build locally:

```bash
# Install Vercel CLI
npm install -g vercel

# Test locally
vercel dev

# Deploy
vercel --prod
```

## Support

- Issues: [GitHub Issues](https://github.com/Animesh-Uttekar/learnlocal/issues)
- Documentation: [Main README](README.md)