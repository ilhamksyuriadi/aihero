"""
Documentation Q&A Agent Application

This package provides tools to create an AI agent that can answer questions
about GitHub repository documentation using RAG (Retrieval-Augmented Generation).
"""

from .ingest import index_data, create_vector_index_from_docs
from .search_tools import SearchTool, setup_vector_search
from .search_agent import init_agent, create_agent_sync
from .logs import ConversationLogger, log_to_file, log_simple_interaction

__version__ = "0.1.0"

__all__ = [
    "index_data",
    "create_vector_index_from_docs",
    "SearchTool",
    "setup_vector_search",
    "init_agent",
    "create_agent_sync",
    "ConversationLogger",
    "log_to_file",
    "log_simple_interaction",
]
