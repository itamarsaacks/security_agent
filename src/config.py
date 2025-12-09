"""Configuration for the SQL injection agent."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
WORKSPACE_DIR = PROJECT_ROOT / "workspace"
KNOWLEDGE_DIR = PROJECT_ROOT / "knowledge"

# Ensure workspace directory exists
WORKSPACE_DIR.mkdir(exist_ok=True)

# File paths
PROGRESS_FILE = WORKSPACE_DIR / "progress.json"
TASKS_FILE = WORKSPACE_DIR / "tasks.json"
KNOWLEDGE_FILE = KNOWLEDGE_DIR / "sqli_techniques.md"

# LLM Configuration
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Choose provider: "anthropic" or "openai"
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "anthropic").lower()

# Model settings per provider
# Cost comparison (per 1M tokens):
# - claude-sonnet-4: $3/$15 (input/output)
# - gpt-4o: $2.50/$10
# - gpt-4o-mini: $0.15/$0.60 (RECOMMENDED for cost savings!)
# - claude-haiku: $0.25/$1.25

ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")  # Much cheaper!
MODEL_TEMPERATURE = 0.1  # Low temperature for consistent reasoning

# Tavily Configuration
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# LangSmith Configuration
LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
LANGSMITH_TRACING = os.getenv("LANGSMITH_TRACING", "true").lower() == "true"
LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", "deep-agents-from-scratch")

# PortSwigger Configuration
PORTSWIGGER_EMAIL = os.getenv("PORTSWIGGER_EMAIL")
PORTSWIGGER_PASSWORD = os.getenv("PORTSWIGGER_PASSWORD")

# Agent Configuration
MAX_ITERATIONS = 200  # Maximum agent iterations (reduced for cost)
CONTEXT_WINDOW_SIZE = 3  # Keep only last 3 messages (progress tracked in files)
REQUEST_DELAY = 0.3  # Delay between requests


def validate_config() -> list[str]:
    """Validate that required configuration is present."""
    errors = []
    
    if not ANTHROPIC_API_KEY:
        errors.append("ANTHROPIC_API_KEY is not set")
    
    if not TAVILY_API_KEY:
        errors.append("TAVILY_API_KEY is not set (optional but recommended)")
    
    if not PORTSWIGGER_EMAIL or not PORTSWIGGER_PASSWORD:
        errors.append("PortSwigger credentials are not set")
    
    return errors

