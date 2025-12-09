"""Progress file management for tracking extraction state."""

import json
from typing import Any
from datetime import datetime
from src.config import PROGRESS_FILE


def get_default_progress() -> dict[str, Any]:
    """Return the default progress structure."""
    return {
        "started_at": None,
        "vulnerability_confirmed": False,
        "target_table": None,
        "target_column": None,
        "target_user": None,
        "password_length": None,
        "extracted_password": "",
        "current_position": 1,
        "query_count": 0,
        "last_updated": None,
        "errors": [],
        "notes": [],
    }


def load_progress() -> dict[str, Any]:
    """Load progress from the filesystem.
    
    Returns:
        The current progress dictionary, or default if file doesn't exist.
    """
    if PROGRESS_FILE.exists():
        try:
            with open(PROGRESS_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return get_default_progress()
    return get_default_progress()


def save_progress(progress: dict[str, Any]) -> None:
    """Save progress to the filesystem.
    
    Args:
        progress: The progress dictionary to save.
    """
    progress["last_updated"] = datetime.now().isoformat()
    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress, f, indent=2)


def reset_progress() -> dict[str, Any]:
    """Reset progress to default state.
    
    Returns:
        The fresh default progress dictionary.
    """
    progress = get_default_progress()
    progress["started_at"] = datetime.now().isoformat()
    save_progress(progress)
    return progress


def update_progress_field(field: str, value: Any) -> dict[str, Any]:
    """Update a single field in the progress file.
    
    Args:
        field: The field name to update.
        value: The new value for the field.
        
    Returns:
        The updated progress dictionary.
    """
    progress = load_progress()
    progress[field] = value
    save_progress(progress)
    return progress


def append_to_password(char: str) -> dict[str, Any]:
    """Append a character to the extracted password.
    
    Args:
        char: The character to append.
        
    Returns:
        The updated progress dictionary.
    """
    progress = load_progress()
    progress["extracted_password"] += char
    progress["current_position"] = len(progress["extracted_password"]) + 1
    save_progress(progress)
    return progress


def increment_query_count() -> int:
    """Increment the query count and return the new value."""
    progress = load_progress()
    progress["query_count"] = progress.get("query_count", 0) + 1
    save_progress(progress)
    return progress["query_count"]


def add_error(error: str) -> None:
    """Add an error to the progress log."""
    progress = load_progress()
    progress["errors"].append({
        "timestamp": datetime.now().isoformat(),
        "error": error
    })
    save_progress(progress)


def add_note(note: str) -> None:
    """Add a note to the progress log."""
    progress = load_progress()
    progress["notes"].append({
        "timestamp": datetime.now().isoformat(),
        "note": note
    })
    save_progress(progress)

