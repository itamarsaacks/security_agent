"""LangGraph definition for the SQL injection agent."""

from typing import Any, Literal
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, AIMessage

from src.state import AgentState
from src.agents.react_agent import create_sqli_agent
from src.tools.browser_tools import get_browser_tools
from src.tools.memory_tools import get_memory_tools
from src.tools.search_tools import get_search_tools
from src.tools.extraction_tools import get_extraction_tools
from src.memory.progress import load_progress
from src.memory.tasks import load_tasks, get_current_task


def load_memory_node(state: AgentState) -> dict[str, Any]:
    """Load the current progress and task state from filesystem.
    
    This node runs before the agent to ensure it has the latest
    persistent state without bloating the conversation history.
    """
    progress = load_progress()
    tasks = load_tasks()
    current_task = get_current_task()
    
    # Create a summary message for the agent
    summary_parts = []
    
    if progress.get("vulnerability_confirmed"):
        summary_parts.append("Vulnerability: CONFIRMED")
    
    if progress.get("password_length"):
        summary_parts.append(f"Password length: {progress['password_length']}")
    
    if progress.get("extracted_password"):
        summary_parts.append(f"Extracted so far: '{progress['extracted_password']}' ({len(progress['extracted_password'])} chars)")
        summary_parts.append(f"Next position: {progress.get('current_position', 1)}")
    
    if progress.get("query_count"):
        summary_parts.append(f"Queries made: {progress['query_count']}")
    
    if current_task:
        summary_parts.append(f"Current task: {current_task}")
    
    return {
        "progress": progress,
        "current_task": current_task,
    }


def should_continue(state: AgentState) -> Literal["continue", "end"]:
    """Determine if the agent should continue or stop.
    
    The agent stops when:
    - The lab is solved
    - Maximum iterations reached
    - The agent decides to stop
    """
    # Check if lab is solved
    if state.get("lab_solved"):
        return "end"
    
    # Check messages for completion indicators
    messages = state.get("messages", [])
    if messages:
        last_message = messages[-1]
        if isinstance(last_message, AIMessage):
            content = last_message.content if isinstance(last_message.content, str) else str(last_message.content)
            if "lab solved" in content.lower() or "congratulations" in content.lower():
                return "end"
    
    return "continue"


def build_graph(checkpointer=None):
    """Build the LangGraph for the SQL injection agent.
    
    Args:
        checkpointer: Optional checkpointer for state persistence.
        
    Returns:
        The compiled graph ready to run.
    """
    # Gather all tools
    tools = (
        get_browser_tools() +
        get_memory_tools() +
        get_search_tools() +
        get_extraction_tools()
    )
    
    # Create the ReAct agent
    react_agent = create_sqli_agent(tools)
    
    # Build the state graph
    # Note: We're using the prebuilt ReAct agent which handles the agent/tools loop internally
    # We wrap it with our memory loading logic
    
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("load_memory", load_memory_node)
    workflow.add_node("agent", react_agent)
    
    # Add edges
    workflow.add_edge(START, "load_memory")
    workflow.add_edge("load_memory", "agent")
    workflow.add_edge("agent", END)
    
    # Compile with optional checkpointer
    if checkpointer:
        return workflow.compile(checkpointer=checkpointer)
    
    return workflow.compile()


def create_checkpointer():
    """Create a memory checkpointer for state persistence.
    
    Returns:
        A MemorySaver checkpointer.
    """
    return MemorySaver()


async def run_agent(
    lab_url: str,
    use_checkpointer: bool = True,
) -> dict[str, Any]:
    """Run the SQL injection agent on a lab.
    
    Args:
        lab_url: The URL of the PortSwigger lab info page. The agent will
                 read the description and access the lab automatically.
        use_checkpointer: Whether to use memory checkpointing.
        
    Returns:
        The final state after the agent completes.
    """
    from src.memory.progress import reset_progress
    from src.memory.tasks import reset_tasks
    
    # Reset memory for fresh start
    reset_progress()
    reset_tasks()
    
    # Create checkpointer if requested
    checkpointer = create_checkpointer() if use_checkpointer else None
    
    # Build the graph
    graph = build_graph(checkpointer)
    
    # Detect if URL is already a lab instance or an info page
    is_lab_instance = "web-security-academy.net" in lab_url
    
    if is_lab_instance:
        # Direct lab instance URL provided
        initial_message = HumanMessage(content=f"""
## Lab Instance URL
{lab_url}

## Your Goal
Extract the administrator's password using blind SQL injection and log in to solve the lab.

## Instructions
The URL is ALREADY a lab instance (web-security-academy.net). Do NOT use access_lab.

1. Read your progress (read_progress) to check existing state
2. Initialize the lab browser (initialize_lab) with the URL above
3. Confirm the vulnerability works (send TRUE and FALSE payloads)
4. Find password length using binary search
5. Extract each character using binary search on ASCII values
6. Submit the password with submit_solution

## Lab Info
- Injection point: TrackingId cookie
- TRUE indicator: "Welcome back" appears
- Table: users, Columns: username, password
- Target user: administrator

Start now!
""")
    else:
        # Info page URL provided
        initial_message = HumanMessage(content=f"""
## Lab Information URL
{lab_url}

## Your Goal
Extract the administrator's password using blind SQL injection and log in to solve the lab.

## Instructions
1. Read your progress (read_progress)
2. Read the lab description (read_lab_description)
3. Access the lab (access_lab) to get a lab instance
4. Then begin exploitation

Work systematically. Good luck!
""")
    
    initial_state = {
        "messages": [initial_message],
        "progress": {},
        "current_task": None,
        "query_count": 0,
        "lab_url": lab_url,
        "lab_solved": False,
    }
    
    # Configuration for the run
    config = {
        "configurable": {
            "thread_id": "sqli-agent-session",
        },
        "recursion_limit": 500,  # Allow many iterations for extraction
    }
    
    # Run the agent
    result = await graph.ainvoke(initial_state, config)
    
    return result

