#!/usr/bin/env python3
"""
Main entry point for LearnerExpert application.
"""

import sys
import os
import logging
from pathlib import Path

def setup_environment():
    """Setup Python path and environment."""
    project_root = Path(__file__).parent
    src_path = project_root / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

def main():
    """Main entry point."""
    setup_environment()
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    logger = logging.getLogger(__name__)
    
    try:
        from learnerexpert.main import app
        from learnerexpert.config.settings import get_settings
        import uvicorn
        
        settings = get_settings()
        
        logger.info("Starting LearnerExpert server...")
        logger.info(f"Server: {settings.api_base_url}")
        logger.info(f"API Docs: {settings.api_base_url}{settings.docs_url}")
        logger.info("Background services will initialize after startup")
        
        uvicorn.run(
            "learnerexpert.main:app",
            host=settings.api_host,
            port=settings.api_port,
            reload=settings.debug,
            log_level=settings.log_level.lower()
        )
        
    except ImportError as e:
        logger.error(f"Import error: {e}")
        logger.error("Ensure dependencies are installed:")
        logger.error("  pip install -r requirements.txt")
        logger.error("Or activate virtual environment:")
        logger.error("  source venv/bin/activate")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()