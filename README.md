# SQL Injection Agent

A multi-agent system using LangGraph to exploit blind SQL injection vulnerabilities with conditional responses.

## Overview

This agent uses the ReAct (Reasoning + Acting) architecture to systematically extract data from a database through blind SQL injection. It's designed for the [PortSwigger Web Security Academy](https://portswigger.net/web-security/sql-injection/blind) blind SQL injection labs.

## Features

- **ReAct Architecture**: The agent reasons about each response and decides the next action
- **Efficient Memory**: Filesystem-based progress tracking to avoid context bloat
- **Binary Search**: Optimized character extraction using ASCII value comparison
- **LangSmith Integration**: Full tracing and evaluation support
- **Playwright Browser**: Proper session and cookie handling
- **Tavily Search**: Web search fallback for SQL syntax lookup

## Setup

### Prerequisites

- **Python 3.8+** installed
- **PortSwigger account** (free): https://portswigger.net/users/register
- **OpenAI API key** OR **Anthropic API key** (at least one required)
  - OpenAI (cheaper): https://platform.openai.com/api-keys
  - Anthropic: https://console.anthropic.com/
- **Optional**: Tavily API key for web search: https://tavily.com/
- **Optional**: LangSmith for tracing: https://smith.langchain.com/

### 1. Clone/Download the Project

```bash
# If you have the project folder
cd security-agent

# If cloning from GitHub
git clone <repo-url>
cd security-agent
```

### 2. Install Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate  # On macOS/Linux
# OR
venv\Scripts\activate     # On Windows

# Install dependencies
pip install -e .

# Install Playwright browsers (required for browser automation)
playwright install chromium
```

**Note**: If `pip install -e .` fails, try: `pip install langgraph langchain langchain-openai langchain-anthropic playwright tavily-python python-dotenv`

### 3. Configure Environment Variables

```bash
# Copy the example file
cp env.example .env

# Open .env in your editor and fill it out
```

**Required variables**:
```env
# Choose ONE provider (or configure both)
LLM_PROVIDER=openai              # or "anthropic"
OPENAI_API_KEY=sk-...            # Get from OpenAI
OPENAI_MODEL=gpt-4o-mini         # Cheapest option (~$0.10/run)

# OR for Anthropic:
# LLM_PROVIDER=anthropic
# ANTHROPIC_API_KEY=sk-ant-...
# ANTHROPIC_MODEL=claude-3-5-haiku-20241022

# Your PortSwigger credentials
PORTSWIGGER_EMAIL=your-email@example.com
PORTSWIGGER_PASSWORD=your-password
```

**Optional variables**:
```env
TAVILY_API_KEY=tvly-...          # For web search (rarely needed)
LANGSMITH_API_KEY=lsv2_...       # For tracing/debugging
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=security_agent
```

### 4. Verify Setup

```bash
# Test that everything is installed
python -c "import langgraph, playwright; print('✅ All good!')"
```

## Usage

### Quick Start

**Option 1: Let the agent access the lab for you** (recommended)
```bash
python main.py "https://portswigger.net/web-security/sql-injection/blind/lab-conditional-responses"
```

**Option 2: Provide a lab instance URL**
1. Go to: https://portswigger.net/web-security/sql-injection/blind/lab-conditional-responses
2. Click "Access the lab"
3. Copy the lab URL (looks like `https://0a1b2c3d.web-security-academy.net/`)
4. Run:
```bash
python main.py "https://0a1b2c3d.web-security-academy.net/"
```

### Advanced Options

```bash
# Without checkpointing (faster but can't resume)
python main.py <URL> --no-checkpointer
```

### Expected Output

```
============================================================
SQL Injection Agent
============================================================
Lab URL: https://...
Started: 2025-12-14T15:00:00

Starting agent...
[Agent will work through the lab...]

============================================================
Agent Completed
============================================================
Vulnerability confirmed: True
Password length: 20
Extracted password: s3cr3tpassw0rd123456
Total queries: 147
Lab solved: True

Completed: 2025-12-14T15:03:00
```

**Time**: ~2-3 minutes  
**Cost**: ~$0.10-0.20 with GPT-4o-mini

## How It Works

### Agent Workflow

1. **Initialize**: Opens the lab in a browser
2. **Confirm Vulnerability**: Tests if TRUE/FALSE conditions produce different responses
3. **Find Password Length**: Binary search to determine password length
4. **Extract Password**: For each position, binary search on ASCII value to find the character
5. **Submit Solution**: Log in with the extracted password

### Efficiency Strategy

- **Filesystem Memory**: Progress is saved to `workspace/progress.json`, allowing the agent to resume and keeping context small
- **Sliding Window**: Only the last 5 messages are kept in conversation history
- **Binary Search**: Reduces character extraction from ~36 tests to ~6 per character
- **Task Queue**: Pre-defined tasks guide the agent without re-reasoning

### Project Structure

```
security-agent/
├── main.py                 # Entry point
├── src/
│   ├── config.py          # Configuration and environment
│   ├── state.py           # LangGraph state definition
│   ├── graph.py           # Graph construction
│   ├── agents/
│   │   └── react_agent.py # ReAct agent with system prompt
│   ├── memory/
│   │   ├── progress.py    # Progress file management
│   │   └── tasks.py       # Task queue management
│   └── tools/
│       ├── browser_tools.py   # Playwright-based tools
│       ├── memory_tools.py    # Progress/task tools
│       └── search_tools.py    # Tavily search tools
├── knowledge/
│   └── sqli_techniques.md # SQL injection knowledge base
└── workspace/
    ├── progress.json      # Extraction progress (generated)
    └── tasks.json         # Task queue (generated)
```

## Evaluation

### Metrics

With LangSmith enabled, you can track:
- **Token usage**: Cost per run
- **Latency**: Time per step
- **Success rate**: Lab completion rate
- **Query count**: Efficiency of extraction

### Manual Metrics

Check `workspace/progress.json` for:
- `query_count`: Total SQL injection attempts
- `errors`: List of failures
- `notes`: Agent observations

### Error Analysis

Common failure modes:
- **Tool failure**: Network/browser errors
- **Logic error**: Incorrect inference from responses
- **Timeout**: Exceeded maximum iterations

## Development

### Running Tests

```bash
pip install -e ".[dev]"
pytest
```

### Customization

- **System Prompt**: Edit `src/agents/react_agent.py` to modify agent behavior
- **Knowledge Base**: Update `knowledge/sqli_techniques.md` for different SQL techniques
- **Tools**: Add new tools in `src/tools/` and register them in `src/graph.py`

## Disclaimer

This tool is for educational purposes only. Only use on systems you have permission to test. The PortSwigger Web Security Academy labs are designed for learning web security.

## Troubleshooting

### "ModuleNotFoundError: No module named 'langgraph'"
```bash
# Make sure virtual environment is activated
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Reinstall dependencies
pip install -e .
```

### "Playwright not found" or browser errors
```bash
# Install Playwright browsers
playwright install chromium
```

### "API key not found" or authentication errors
- Double-check your `.env` file exists (not `.env.example`)
- Verify API keys are correct (no extra spaces/quotes)
- For OpenAI: Key should start with `sk-`
- For Anthropic: Key should start with `sk-ant-`

### "Could not access lab" or "Login failed"
- Verify PortSwigger email/password in `.env` are correct
- Try logging into PortSwigger website manually first
- Make sure you have an active internet connection

### Agent runs but finds no password
- Check `workspace/progress.json` for errors
- Look at LangSmith trace if enabled
- Try running again (sometimes labs timeout)

### High costs / running out of credits
- Use `LLM_PROVIDER=openai` with `OPENAI_MODEL=gpt-4o-mini` (cheapest)
- Each run should cost ~$0.10-0.20
- Anthropic models are more expensive

### Need help?
- Check `workspace/progress.json` for detailed error logs
- Enable LangSmith tracing to see what the agent is doing
- Open an issue on GitHub with your error message

