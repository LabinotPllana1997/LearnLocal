"""
LearnerExpert: AI-powered L&D Multi-Agent System

A comprehensive learning and development automation system using LangGraph
for curriculum validation, quiz generation, and content enrichment.
"""

__version__ = "0.1.0"
__author__ = "LearnerExpert Team"

from .agents.graph import get_graph
from .config.settings import get_settings

__all__ = ["get_graph", "get_settings"]