"""Destination Research Agent - Gathers information about travel destinations."""

from strands import Agent
from .base import create_agent, web_search, get_current_date

SYSTEM_PROMPT = """You are a destination research specialist. Your job is to gather comprehensive information about travel destinations.

When researching a destination, provide:
1. **Best time to visit** - Weather, crowds, events
2. **Key areas/neighborhoods** - Where to stay, what each area offers
3. **Local customs & tips** - Cultural notes, etiquette, practical advice
4. **Budget considerations** - Cost of living, typical expenses
5. **Safety information** - Any travel advisories or precautions

Use the web_search tool to find current information.
Be concise but thorough. Focus on actionable insights for trip planning."""


def create_researcher_agent() -> Agent:
    """Create the destination researcher agent."""
    return create_agent(
        system_prompt=SYSTEM_PROMPT,
        tools=[web_search, get_current_date],
        temperature=0.3
    )


def research_destination(destination: str, travel_dates: str, preferences: str = "") -> str:
    """
    Research a destination and return comprehensive travel information.

    Args:
        destination: The travel destination
        travel_dates: When the user plans to travel
        preferences: Optional user preferences

    Returns:
        Destination research summary
    """
    agent = create_researcher_agent()

    prompt = f"""Research this destination for a traveler:

**Destination:** {destination}
**Travel Dates:** {travel_dates}
**Preferences:** {preferences if preferences else "None specified"}

Provide a comprehensive research summary to help plan this trip."""

    response = agent(prompt)
    return str(response)
