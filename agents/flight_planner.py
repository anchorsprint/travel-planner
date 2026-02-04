"""Flight Planner Agent - Finds and recommends flight options."""

from strands import Agent
from .base import create_agent, web_search

SYSTEM_PROMPT = """You are a flight planning specialist. Your job is to find and recommend flight options.

When planning flights, consider:
1. **Direct vs connecting flights** - Trade-offs between time and cost
2. **Departure times** - Morning, afternoon, red-eye options
3. **Airlines** - Reputation, baggage policies, amenities
4. **Airports** - If multiple airports serve the destination
5. **Price estimates** - Budget, economy, premium options

Provide 2-3 flight options with pros/cons for each.
Use web_search to find current flight information and prices.
Format clearly with departure/arrival times and estimated costs."""


def create_flight_agent() -> Agent:
    """Create the flight planner agent."""
    return create_agent(
        system_prompt=SYSTEM_PROMPT,
        tools=[web_search],
        temperature=0.3
    )


def plan_flights(
    origin: str,
    destination: str,
    departure_date: str,
    return_date: str,
    travelers: int = 1,
    budget: str = "moderate"
) -> str:
    """
    Find flight options for the trip.

    Args:
        origin: Departure city/airport
        destination: Arrival city/airport
        departure_date: Outbound flight date
        return_date: Return flight date
        travelers: Number of travelers
        budget: Budget level (budget/moderate/premium)

    Returns:
        Flight recommendations
    """
    agent = create_flight_agent()

    prompt = f"""Find flight options for this trip:

**From:** {origin}
**To:** {destination}
**Departure:** {departure_date}
**Return:** {return_date}
**Travelers:** {travelers}
**Budget:** {budget}

Provide 2-3 flight options with estimated prices, times, and airlines.
Include both budget-friendly and convenient options."""

    response = agent(prompt)
    return str(response)
