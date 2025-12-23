"""
Tool registry for agent operations.
"""

from typing import Dict, List
from utils.logger import get_logger

logger = get_logger(__name__)


class ToolRegistry:
    """Simulates available tools for the agent."""
    
    @staticmethod
    def web_search(query: str) -> str:
        """Simulates web search - returns mock results."""
        return f"[SEARCH RESULTS for '{query}']: Found 5 relevant articles about {query}. Top result discusses key aspects including recent developments, expert opinions, and statistical data."
    
    @staticmethod
    def web_fetch(url: str) -> str:
        """Simulates fetching a webpage."""
        return f"[WEBPAGE CONTENT from {url}]: Detailed information about the topic including comprehensive statistics, expert opinions, recent developments, and in-depth analysis."
    
    @staticmethod
    def get_tool_descriptions() -> List[Dict[str, str]]:
        """Returns tool descriptions for the agent."""
        return [
            {
                "name": "web_search",
                "description": "Searches the web for information. Use this when you need to find current information or multiple sources. Required for questions about recent events, current data, or topics you're unsure about.",
                "parameters": "query (str): The search query"
            },
            {
                "name": "web_fetch",
                "description": "Fetches detailed content from a specific URL. Use this AFTER web_search to get detailed information from relevant sources. Do not use without searching first.",
                "parameters": "url (str): The URL to fetch"
            }
        ]

