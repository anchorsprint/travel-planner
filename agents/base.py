"""Base agent utilities and shared tools."""

from strands import Agent, tool
from strands.models import OpenAIModel
from config import DEFAULT_MODEL, FAST_MODEL, TEMPERATURE_FACTUAL, TEMPERATURE_CREATIVE


def create_agent(
    system_prompt: str,
    model_id: str = DEFAULT_MODEL,
    temperature: float = TEMPERATURE_FACTUAL,
    tools: list = None
) -> Agent:
    """Create a Strands agent with consistent configuration."""
    return Agent(
        model=OpenAIModel(
            model_id=model_id,
            params={"temperature": temperature}
        ),
        system_prompt=system_prompt,
        tools=tools or []
    )


@tool
def web_search(query: str) -> str:
    """
    Search the web for travel information.

    Args:
        query: Search query for travel-related information

    Returns:
        Search results as formatted text
    """
    # Placeholder - in production, integrate with actual search API
    # Options: Tavily, SerpAPI, Brave Search, or Google Custom Search
    return f"[Web Search Results for: {query}]\n\nNote: Web search integration pending. Using model knowledge for now."


@tool
def get_current_date() -> str:
    """Get the current date for planning purposes."""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d")
