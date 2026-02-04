"""Itinerary Synthesizer Agent - Combines all research into coherent travel plans."""

from strands import Agent
from .base import create_agent
from config import TEMPERATURE_CREATIVE

SYSTEM_PROMPT = """You are a master travel itinerary designer. Your job is to synthesize research from multiple specialists into coherent, day-by-day travel plans.

You will receive:
- Destination research
- Flight options
- Hotel recommendations
- Activity suggestions

Your task is to create **2 distinct itinerary options**:

**Option A:** Focus on one theme (e.g., cultural immersion, relaxation, adventure)
**Option B:** Different theme or approach (e.g., budget-friendly, luxury, fast-paced)

For each option, provide:
1. **Theme/Style** - What makes this option unique
2. **Recommended flight & hotel** - Pick the best match for this theme
3. **Day-by-day schedule** - Morning, afternoon, evening activities
4. **Estimated total cost** - Breakdown by category
5. **Best for** - Who this option suits

Make the itineraries practical and realistic:
- Account for jet lag on arrival day
- Include meal recommendations
- Allow buffer time between activities
- Note any reservations needed

Format clearly with headers and bullet points."""


def create_synthesizer_agent() -> Agent:
    """Create the itinerary synthesizer agent."""
    return create_agent(
        system_prompt=SYSTEM_PROMPT,
        temperature=TEMPERATURE_CREATIVE
    )


def synthesize_itinerary(
    destination_research: str,
    flight_options: str,
    hotel_options: str,
    activity_options: str,
    user_request: str
) -> str:
    """
    Synthesize all research into complete itinerary options.

    Args:
        destination_research: Research about the destination
        flight_options: Flight recommendations
        hotel_options: Hotel recommendations
        activity_options: Activity recommendations
        user_request: Original user request for context

    Returns:
        Two complete itinerary options
    """
    agent = create_synthesizer_agent()

    prompt = f"""Create 2 complete travel itinerary options based on this research:

## Original Request
{user_request}

## Destination Research
{destination_research}

## Flight Options
{flight_options}

## Hotel Options
{hotel_options}

## Activity Options
{activity_options}

---

Now synthesize this into **2 distinct itinerary options** (Option A and Option B).
Each should have a clear theme, day-by-day schedule, and total cost estimate.
Make them meaningfully different so the traveler has a real choice."""

    response = agent(prompt)
    return str(response)
