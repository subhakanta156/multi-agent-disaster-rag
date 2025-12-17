"""
Web Search Tool - Uses Serper.dev (Google Search API)
Compatible with LangGraph + @tool system.
"""

from langchain.tools import tool
import requests
import os


@tool
def web_search_tool(query: str) -> str:
    """
    Perform intelligent Google search using Serper API.
    
    Requires:
        SERPER_API_KEY in .env file
    
    Args:
        query (str): Search query
    
    Returns:
        str: Formatted search results
    """
    query = query.strip()
    if not query:
        return "Error: No search query provided."

    # 🔥 Load API key dynamically AFTER .env is loaded in workflow.py
    api_key = os.getenv("SERPER_API_KEY")

    if not api_key:
        return "Error: SERPER_API_KEY not found. Add it in your .env file."

    try:
        # Google search endpoint
        url = "https://google.serper.dev/search"

        headers = {
            "X-API-KEY": api_key,
            "Content-Type": "application/json"
        }

        payload = {
            "q": query,
            "num": 5  # limit results
        }

        response = requests.post(url, json=payload, headers=headers, timeout=10)

        if response.status_code != 200:
            return f"Serper API error: HTTP {response.status_code} – {response.text}"

        data = response.json()

        # "organic" results are the primary search results
        results = data.get("organic", [])

        if not results:
            return "No search results found."

        return _format_results(results)

    except requests.Timeout:
        return "Search error: Request timed out."

    except Exception as e:
        return f"Search error: {str(e)}"


def _format_results(results: list) -> str:
    """Format Serper search results into readable text."""
    output = []

    for i, item in enumerate(results, 1):
        title = item.get("title", "No title")
        snippet = item.get("snippet", "No description available")
        link = item.get("link", "No URL found")

        formatted = (
            f"{i}. {title}\n"
            f"   {snippet}\n"
            f"   URL: {link}"
        )

        output.append(formatted)

    return "\n\n".join(output)
