#!/usr/bin/env python3
"""Main entry point for the SQL injection agent."""

import asyncio
import argparse
import sys
from datetime import datetime

from src.config import validate_config, LANGSMITH_TRACING, LANGSMITH_PROJECT
from src.graph import run_agent
from src.memory.progress import load_progress
from src.tools.browser_tools import close_browser_async


async def main():
    """Main function to run the SQL injection agent."""
    parser = argparse.ArgumentParser(
        description="Run the SQL injection agent on a PortSwigger lab"
    )
    parser.add_argument(
        "lab_url",
        help="The URL of the PortSwigger lab info page (e.g., https://portswigger.net/web-security/sql-injection/blind/lab-conditional-responses)"
    )
    parser.add_argument(
        "--no-checkpointer",
        action="store_true",
        help="Disable SQLite checkpointing"
    )
    
    args = parser.parse_args()
    
    # Validate configuration
    print("Validating configuration...")
    errors = validate_config()
    if errors:
        print("Configuration errors:")
        for error in errors:
            print(f"  - {error}")
        if "ANTHROPIC_API_KEY" in str(errors):
            print("\nCannot proceed without ANTHROPIC_API_KEY.")
            sys.exit(1)
    
    # Set up LangSmith tracing
    if LANGSMITH_TRACING:
        import os
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_PROJECT"] = LANGSMITH_PROJECT
        print(f"LangSmith tracing enabled (project: {LANGSMITH_PROJECT})")
    
    print(f"\n{'='*60}")
    print("SQL Injection Agent")
    print(f"{'='*60}")
    print(f"Lab URL: {args.lab_url}")
    print(f"Started: {datetime.now().isoformat()}")
    print(f"{'='*60}\n")
    
    try:
        # Run the agent
        print("Starting agent...")
        result = await run_agent(
            lab_url=args.lab_url,
            use_checkpointer=not args.no_checkpointer,
        )
        
        # Print results
        print(f"\n{'='*60}")
        print("Agent Completed")
        print(f"{'='*60}")
        
        # Load final progress
        progress = load_progress()
        
        print(f"Vulnerability confirmed: {progress.get('vulnerability_confirmed', False)}")
        print(f"Password length: {progress.get('password_length', 'Unknown')}")
        print(f"Extracted password: {progress.get('extracted_password', 'None')}")
        print(f"Total queries: {progress.get('query_count', 0)}")
        print(f"Lab solved: {progress.get('lab_solved', False)}")
        
        if progress.get("errors"):
            print(f"\nErrors encountered: {len(progress['errors'])}")
            for err in progress["errors"][-5:]:  # Show last 5 errors
                print(f"  - {err.get('error', err)}")
        
        print(f"\nCompleted: {datetime.now().isoformat()}")
        
    except KeyboardInterrupt:
        print("\n\nAgent interrupted by user.")
        progress = load_progress()
        print(f"Progress saved. Extracted so far: '{progress.get('extracted_password', '')}'")
        
    except Exception as e:
        print(f"\nError: {e}")
        raise
        
    finally:
        # Clean up browser
        print("\nClosing browser...")
        await close_browser_async()
        print("Done.")


if __name__ == "__main__":
    asyncio.run(main())

