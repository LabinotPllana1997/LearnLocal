"""
Main FastAPI application for LearnerExpert with offline capabilities.
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from .config.settings import get_settings
from .database import init_database, close_database
from .api.endpoints.offline_endpoints import router as offline_router

logger = logging.getLogger(__name__)
settings = get_settings()

app = FastAPI(
    title="LearnerExpert",
    description="AI-powered multi-agent L&D system for curriculum validation, quiz generation, and content enrichment",
    version="1.0.0",
    docs_url=settings.docs_url,
    redoc_url="/redoc" if settings.debug else None
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.frontend_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(offline_router)

@app.on_event("startup")
async def startup_event():
    await init_database()
    settings.ensure_directories()
    logger.info("Database initialized")
    logger.info("LearnerExpert backend started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    await close_database()
    logger.info("Database connection closed")

@app.get("/")
async def root():
    return {
        "message": "LearnerExpert Educational Assistant",
        "status": "online",
        "features": [
            "Offline LLM with GPT-OSS-20B",
            "Text-to-Speech",
            "Educational Content Generation",
            "Analytics and History"
        ]
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "All services operational"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    )