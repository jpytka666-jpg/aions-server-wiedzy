"""
MARCIN MEMORY MCP - Persistent Memory Server for Claude
========================================================
Local permanent memory system with automatic context injection.

Design principles:
- Auto-load relevant context at conversation start
- Compress old memories to save tokens
- Domain-based organization (KLES-style)
- Semantic search for retrieval
"""

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from enum import Enum
from contextlib import asynccontextmanager
import json
import os
from datetime import datetime
from pathlib import Path

# Import our memory modules
from memory.storage import MemoryStorage
from memory.retriever import MemoryRetriever
from memory.compressor import MemoryCompressor
from memory.domains import DomainManager

# Configuration
DATA_DIR = Path(__file__).parent / "data"
CONFIG_FILE = Path(__file__).parent / "config.yaml"
