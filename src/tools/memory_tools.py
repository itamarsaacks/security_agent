"""Memory management tools for the agent to track progress."""

from typing import Any
from langchain_core.tools import tool

from src.memory.progress import (
    load_progress,
    update_progress_field,
    append_to_password,
    add_note,
    reset_progress,
)
from src.memory.tasks import (
    load_tasks,
    get_current_task,
    complete_current_task,
    add_character_extraction_tasks,
    get_task_summary,
    reset_tasks,
)
from src.config import KNOWLEDGE_FILE


@tool
def read_progress() -> dict[str, Any]:
    """Read the current extraction progress from persistent storage.
    
    Returns:
        A dictionary containing all progress information including:
        - vulnerability_confirmed: Whether SQLi vulnerability is confirmed
        - password_length: Length of the target password (if known)
        - extracted_password: Characters extracted so far
        - current_position: Next character position to extract
        - query_count: Total SQL injection queries made
    """
    return load_progress()


@tool
def update_progress(field: str, value: Any) -> dict[str, Any]:
    """Update a specific field in the progress tracker.
    
    Args:
        field: The field name to update. Valid fields include:
               - vulnerability_confirmed (bool)
               - target_table (str)
               - target_column (str)
               - target_user (str)
               - password_length (int)
               - extracted_password (str)
               - current_position (int)
        value: The new value for the field.
        
    Returns:
        The updated progress dictionary.
    """
    return update_progress_field(field, value)


@tool
def record_extracted_character(character: str) -> dict[str, Any]:
    """Record a newly extracted character and update position.
    
    Use this after successfully determining a character of the password.
    
    Args:
        character: The single character that was extracted.
        
    Returns:
        The updated progress dictionary with the new password state.
    """
    return append_to_password(character)


@tool
def add_progress_note(note: str) -> str:
    """Add a note to the progress log for debugging/analysis.
    
    Args:
        note: A note describing an observation or decision.
        
    Returns:
        Confirmation message.
    """
    add_note(note)
    return f"Note recorded: {note}"


@tool
def get_current_task_info() -> dict[str, Any]:
    """Get information about the current task and overall progress.
    
    Returns:
        A dictionary with:
        - current_task: The task currently being worked on
        - summary: A summary of completed/pending tasks
        - all_tasks: The full task structure
    """
    tasks = load_tasks()
    return {
        "current_task": get_current_task(),
        "summary": get_task_summary(),
        "completed": [t["task"] if isinstance(t, dict) else t for t in tasks["completed"]],
        "pending": tasks["pending"],
    }


@tool
def mark_task_complete() -> dict[str, Any]:
    """Mark the current task as complete and move to the next task.
    
    Returns:
        A dictionary with the new current task.
    """
    new_task = complete_current_task()
    return {
        "completed": True,
        "new_current_task": new_task,
        "summary": get_task_summary(),
    }


@tool
def setup_character_extraction(password_length: int) -> dict[str, Any]:
    """Set up individual tasks for extracting each character of the password.
    
    Call this after determining the password length to create a task
    for each character position.
    
    Args:
        password_length: The length of the password to extract.
        
    Returns:
        Information about the created tasks.
    """
    add_character_extraction_tasks(password_length)
    tasks = load_tasks()
    return {
        "tasks_created": password_length,
        "pending_tasks": tasks["pending"][:10],  # Show first 10
        "message": f"Created {password_length} character extraction tasks"
    }


@tool
def reset_agent_memory() -> dict[str, str]:
    """Reset all progress and tasks to start fresh.
    
    Use this to start a new extraction attempt from scratch.
    
    Returns:
        Confirmation message.
    """
    reset_progress()
    reset_tasks()
    return {
        "status": "Memory reset",
        "message": "Progress and tasks have been reset. Ready to start fresh."
    }


@tool
def read_knowledge_file() -> str:
    """Read the SQL injection knowledge base for reference.
    
    This file contains techniques and strategies for blind SQL injection.
    Read this when you need guidance on SQL injection methodology.
    
    Returns:
        The contents of the knowledge file.
    """
    if KNOWLEDGE_FILE.exists():
        with open(KNOWLEDGE_FILE, "r") as f:
            return f.read()
    return "Knowledge file not found."


def get_memory_tools() -> list:
    """Get all memory-related tools."""
    return [
        read_progress,
        update_progress,
        record_extracted_character,
        add_progress_note,
        get_current_task_info,
        mark_task_complete,
        setup_character_extraction,
        reset_agent_memory,
        read_knowledge_file,
    ]

