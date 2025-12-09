"""State definition for the SQL injection agent graph."""

from typing import Annotated, Any
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages


def sliding_window_messages(existing: list, new: list) -> list:
    """Keep only the last N messages in the conversation.
    
    This reducer maintains a sliding window of messages to prevent
    context from growing unbounded during long extraction sessions.
    """
    from src.config import CONTEXT_WINDOW_SIZE
    
    # Combine existing and new messages
    combined = add_messages(existing, new)
    
    # Keep system message (if present) + last N messages
    if combined and hasattr(combined[0], 'type') and combined[0].type == "system":
        system_msg = [combined[0]]
        other_msgs = combined[1:]
        return system_msg + other_msgs[-CONTEXT_WINDOW_SIZE:]
    
    return combined[-CONTEXT_WINDOW_SIZE:]


class AgentState(TypedDict):
    """State for the SQL injection agent.
    
    Attributes:
        messages: Conversation history (sliding window)
        progress: Current extraction progress loaded from filesystem
        current_task: The current task being worked on
        query_count: Total number of SQL injection queries made
        lab_url: The URL of the PortSwigger lab
        lab_solved: Whether the lab has been solved
    """
    messages: Annotated[list, sliding_window_messages]
    progress: dict[str, Any]
    current_task: str | None
    query_count: int
    lab_url: str
    lab_solved: bool


def create_initial_state(lab_url: str) -> AgentState:
    """Create the initial state for a new agent run."""
    return AgentState(
        messages=[],
        progress={},
        current_task=None,
        query_count=0,
        lab_url=lab_url,
        lab_solved=False,
    )

