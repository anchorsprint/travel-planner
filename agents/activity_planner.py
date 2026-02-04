"""Activity Planner Agent - Curates activities, attractions, and experiences."""

from strands import Agent
from .base import create_agent, web_search

SYSTEM_PROMPT = """You are a local experiences specialist. Your job is to curate activities, attractions, restaurants, and experiences.

When planning activities, consider:
1. **Must-see attractions** - Iconic landmarks, popular spots
2. **Hidden gems** - Local favorites, off-the-beaten-path experiences
3. **Food & dining** - Restaurants, street food, food tours
4. **Cultural experiences** - Museums, shows, local traditions
5. **Day trips** - Nearby excursions worth considering

Organize activities by category and include:
- Estimated time needed
- Approximate cost
- Best time to visit
- Booking requirements (if any)

Use web_search to find current information about attractions and restaurants."""

FAMILY_SYSTEM_PROMPT = """You are a FAMILY travel experiences specialist. Your job is to curate KID-FRIENDLY activities, attractions, restaurants, and experiences.

**CRITICAL:** All recommendations must be suitable for children. Consider:
- Age-appropriateness of activities
- Safety for children
- Stroller/wheelchair accessibility
- Kid-friendly dining options (high chairs, kids menu)
- Attention span of children (shorter activities for younger kids)
- Interactive and engaging experiences
- Rest/nap opportunities
- Bathroom/changing facilities

When planning activities:
1. **Family Attractions** - Theme parks, zoos, aquariums, interactive museums
2. **Parks & Playgrounds** - Outdoor spaces for kids to play
3. **Family Dining** - Restaurants that welcome children
4. **Educational Fun** - Museums with hands-on exhibits
5. **Easy Day Trips** - Short, manageable excursions

Mark each activity with:
- Age suitability (e.g., "Best for ages 5+")
- Kid-friendliness rating (1-5 stars)
- Stroller accessibility
- Estimated duration for families"""


def create_activity_agent(family_mode: bool = False) -> Agent:
    """Create the activity planner agent."""
    prompt = FAMILY_SYSTEM_PROMPT if family_mode else SYSTEM_PROMPT
    return create_agent(
        system_prompt=prompt,
        tools=[web_search],
        temperature=0.6  # Slightly more creative for activity suggestions
    )


def plan_activities(
    destination: str,
    duration_days: int,
    interests: str = "",
    budget: str = "moderate",
    family_filter: str = "",
    kid_ages: list[int] = None
) -> str:
    """
    Curate activities and experiences for the trip.

    Args:
        destination: Travel destination
        duration_days: Length of stay in days
        interests: User interests (food, culture, adventure, etc.)
        budget: Budget level
        family_filter: Family-specific filtering instructions
        kid_ages: Ages of children (triggers family mode)

    Returns:
        Curated activity recommendations
    """
    is_family = bool(kid_ages) or bool(family_filter)
    agent = create_activity_agent(family_mode=is_family)

    # Build family context
    family_section = ""
    if kid_ages:
        ages_str = ", ".join(str(age) for age in kid_ages)
        family_section = f"""
**FAMILY TRAVEL - Children's Ages:** {ages_str}
{family_filter}

⚠️ All activities MUST be suitable for children. Prioritize:
- Safety and accessibility
- Kid-friendly venues
- Appropriate duration for young travelers
- Fun and engaging experiences
"""

    prompt = f"""Curate activities and experiences for this trip:

**Destination:** {destination}
**Duration:** {duration_days} days
**Interests:** {interests if interests else "General sightseeing, food, culture"}
**Budget:** {budget}
{family_section}

Provide a comprehensive list of:
1. {"Family-friendly attractions (top 5-7)" if is_family else "Must-see attractions (top 5-7)"}
2. {"Family restaurants with kids menu (3-5)" if is_family else "Restaurant recommendations (3-5, different styles)"}
3. {"Fun experiences for kids (2-3)" if is_family else "Unique local experiences (2-3)"}
4. {"Easy day trips suitable for children (1-2)" if is_family else "Optional day trips (1-2)"}

Include practical details like costs, timing, and booking tips."""

    response = agent(prompt)
    return str(response)
