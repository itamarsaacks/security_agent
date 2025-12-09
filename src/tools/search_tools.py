"""Web search tools using Tavily for researching SQL injection techniques."""

from langchain_core.tools import tool
from tavily import TavilyClient

from src.config import TAVILY_API_KEY


def get_tavily_client() -> TavilyClient | None:
    """Get the Tavily client if API key is configured."""
    if TAVILY_API_KEY:
        return TavilyClient(api_key=TAVILY_API_KEY)
    return None


@tool
def search_sql_technique(query: str) -> str:
    """Search the web for SQL injection techniques and database syntax.
    
    Use this tool when you need to:
    - Look up specific SQL syntax for a database
    - Research SQL injection techniques you're unsure about
    - Find examples of blind SQL injection payloads
    
    Args:
        query: The search query. Be specific, e.g., 
               "PostgreSQL SUBSTRING function syntax" or
               "blind SQL injection binary search technique"
               
    Returns:
        Search results with relevant information.
    """
    client = get_tavily_client()
    
    if client is None:
        return "Tavily API key not configured. Cannot perform web search."
    
    try:
        # Add context to the query for better results
        enhanced_query = f"SQL injection {query}"
        
        response = client.search(
            query=enhanced_query,
            search_depth="basic",
            max_results=3,
        )
        
        # Format the results
        results = []
        for result in response.get("results", []):
            results.append(f"**{result.get('title', 'No title')}**\n{result.get('content', 'No content')}\nSource: {result.get('url', 'No URL')}\n")
        
        if results:
            return "\n---\n".join(results)
        else:
            return "No results found for your query."
            
    except Exception as e:
        return f"Search failed: {str(e)}"


@tool
def search_database_syntax(database_type: str, function_name: str) -> str:
    """Search for specific database function syntax.
    
    Use this when you need to know the exact syntax for a SQL function
    in a specific database system.
    
    Args:
        database_type: The database type (e.g., "PostgreSQL", "MySQL", "Oracle")
        function_name: The function to look up (e.g., "SUBSTRING", "LENGTH", "ASCII")
        
    Returns:
        Information about the function syntax.
    """
    client = get_tavily_client()
    
    if client is None:
        return "Tavily API key not configured. Cannot perform web search."
    
    try:
        query = f"{database_type} {function_name} function syntax SQL"
        
        response = client.search(
            query=query,
            search_depth="basic",
            max_results=2,
        )
        
        results = []
        for result in response.get("results", []):
            results.append(f"**{result.get('title', 'No title')}**\n{result.get('content', 'No content')}\n")
        
        if results:
            return "\n---\n".join(results)
        else:
            return f"No results found for {database_type} {function_name}."
            
    except Exception as e:
        return f"Search failed: {str(e)}"


def get_search_tools() -> list:
    """Get all search-related tools."""
    return [search_sql_technique, search_database_syntax]

