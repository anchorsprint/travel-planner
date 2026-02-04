"""Hotel Planner Agent - Finds and recommends accommodation options."""

from strands import Agent
from .base import create_agent, web_search

SYSTEM_PROMPT = """You are an accommodation specialist. Your job is to find and recommend hotels and lodging options.

When recommending accommodations, consider:
1. **Location** - Proximity to attractions, transport, safety
2. **Property types** - Hotels, boutique stays, apartments, hostels
3. **Amenities** - WiFi, breakfast, pool, gym, etc.
4. **Reviews & ratings** - Guest satisfaction
5. **Price range** - Per night costs, total stay cost

Provide 2-3 accommodation options at different price points.
Use web_search to find current availability and prices.
Explain why each option suits the traveler's needs."""


def create_hotel_agent() -> Agent:
    """Create the hotel planner agent."""
    return create_agent(
        system_prompt=SYSTEM_PROMPT,
        tools=[web_search],
        temperature=0.3
    )


def plan_hotels(
    destination: str,
    check_in: str,
    check_out: str,
    travelers: int = 1,
    budget: str = "moderate",
    preferences: str = ""
) -> str:
    """
    Find hotel options for the trip.

    Args:
        destination: City/area to stay
        check_in: Check-in date
        check_out: Check-out date
        travelers: Number of travelers
        budget: Budget level (budget/moderate/luxury)
        preferences: Location or amenity preferences

    Returns:
        Hotel recommendations
    """
    agent = create_hotel_agent()

    prompt = f"""Find accommodation options:

**Destination:** {destination}
**Check-in:** {check_in}
**Check-out:** {check_out}
**Travelers:** {travelers}
**Budget:** {budget}
**Preferences:** {preferences if preferences else "None specified"}

Provide 2-3 accommodation options. Include:
- Property name and type
- Location/neighborhood
- Key amenities
- Estimated price per night
- Why it's a good fit"""

    response = agent(prompt)
    return str(response)
