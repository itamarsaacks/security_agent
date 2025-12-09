"""Task queue management for tracking agent progress."""

import json
from typing import Any
from datetime import datetime
from src.config import TASKS_FILE


def get_default_tasks() -> dict[str, Any]:
    """Return the default task structure."""
    return {
        "completed": [],
        "current": None,
        "pending": [],
        "created_at": None,
        "last_updated": None,
    }


def load_tasks() -> dict[str, Any]:
    """Load tasks from the filesystem.
    
    Returns:
        The current tasks dictionary, or default if file doesn't exist.
    """
    if TASKS_FILE.exists():
        try:
            with open(TASKS_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return get_default_tasks()
    return get_default_tasks()


def save_tasks(tasks: dict[str, Any]) -> None:
    """Save tasks to the filesystem.
    
    Args:
        tasks: The tasks dictionary to save.
    """
    tasks["last_updated"] = datetime.now().isoformat()
    with open(TASKS_FILE, "w") as f:
        json.dump(tasks, f, indent=2)


def reset_tasks() -> dict[str, Any]:
    """Reset tasks to default state with initial task list.
    
    Returns:
        The fresh tasks dictionary with initial tasks.
    """
    tasks = get_default_tasks()
    tasks["created_at"] = datetime.now().isoformat()
    tasks["pending"] = [
        "read_lab_description",
        "access_lab",
        "confirm_vulnerability",
        "find_password_length",
        "extract_password",
        "submit_solution",
    ]
    tasks["current"] = tasks["pending"].pop(0)
    save_tasks(tasks)
    return tasks


def get_current_task() -> str | None:
    """Get the current task being worked on.
    
    Returns:
        The current task name, or None if no tasks remain.
    """
    tasks = load_tasks()
    return tasks.get("current")


def complete_current_task() -> str | None:
    """Mark the current task as complete and move to the next.
    
    Returns:
        The new current task, or None if all tasks are complete.
    """
    tasks = load_tasks()
    
    if tasks["current"]:
        tasks["completed"].append({
            "task": tasks["current"],
            "completed_at": datetime.now().isoformat()
        })
    
    if tasks["pending"]:
        tasks["current"] = tasks["pending"].pop(0)
    else:
        tasks["current"] = None
    
    save_tasks(tasks)
    return tasks["current"]


def add_task(task: str, position: int | None = None) -> None:
    """Add a new task to the pending queue.
    
    Args:
        task: The task name to add.
        position: Optional position to insert at (default: end).
    """
    tasks = load_tasks()
    
    if position is not None:
        tasks["pending"].insert(position, task)
    else:
        tasks["pending"].append(task)
    
    save_tasks(tasks)


def add_character_extraction_tasks(password_length: int) -> None:
    """Add tasks for extracting each character of the password.
    
    Args:
        password_length: The length of the password to extract.
    """
    tasks = load_tasks()
    
    # Remove the generic "extract_password" task if present
    tasks["pending"] = [t for t in tasks["pending"] if t != "extract_password"]
    
    # Add individual character extraction tasks
    char_tasks = [f"extract_char_{i}" for i in range(1, password_length + 1)]
    
    # Insert before submit_solution if present
    if "submit_solution" in tasks["pending"]:
        idx = tasks["pending"].index("submit_solution")
        tasks["pending"] = tasks["pending"][:idx] + char_tasks + tasks["pending"][idx:]
    else:
        tasks["pending"].extend(char_tasks)
    
    save_tasks(tasks)


def get_task_summary() -> str:
    """Get a summary of task progress.
    
    Returns:
        A formatted string summarizing task progress.
    """
    tasks = load_tasks()
    completed_count = len(tasks["completed"])
    pending_count = len(tasks["pending"])
    current = tasks["current"] or "None"
    
    return (
        f"Completed: {completed_count} | "
        f"Current: {current} | "
        f"Pending: {pending_count}"
    )

