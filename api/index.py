"""
Vercel deployment entry point for LearnLocal API.
"""

import sys
import os
from pathlib import Path

# Add src to Python path
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Import the FastAPI app
from learnlocal.main import app

# Export for Vercel
handler = app