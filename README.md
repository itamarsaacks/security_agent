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

### 1. Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .

# Install Playwright browsers
playwright install chromium
```

### 2. Configure Environment

Copy `env.example` to `.env` and fill in your API keys:

```bash
cp env.example .env
```

Required variables:
- `ANTHROPIC_API_KEY`: Your Anthropic API key for Claude
- `PORTSWIGGER_EMAIL`: Your PortSwigger account email
- `PORTSWIGGER_PASSWORD`: Your PortSwigger account password

Optional:
- `TAVILY_API_KEY`: For web search functionality
- `LANGSMITH_API_KEY`: For tracing and evaluation

### 3. Start a Lab

1. Go to [PortSwigger Web Security Academy](https://portswigger.net/web-security/sql-injection/blind/lab-conditional-responses)
2. Click "Access the lab" to start a new lab instance
3. Copy the lab URL (e.g., `https://xxxxx.web-security-academy.net/`)

## Usage

```bash
# Run the agent on a lab
python main.py "https://YOUR-LAB-ID.web-security-academy.net/"

# With custom description
python main.py "https://YOUR-LAB-ID.web-security-academy.net/" -d "Custom lab description"

# Without checkpointing
python main.py "https://YOUR-LAB-ID.web-security-academy.net/" --no-checkpointer
```

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

