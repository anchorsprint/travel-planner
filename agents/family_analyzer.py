"""Family Analyzer Agent - Analyzes family needs and sets constraints for kid-friendly travel."""

from pydantic import BaseModel, Field
from strands import Agent
from .base import create_agent
from .intents import TravelContext

SYSTEM_PROMPT = """You are a family travel specialist. Your job is to analyze family composition and set appropriate travel constraints for a safe, enjoyable trip with children.

When analyzing family needs, consider:

**By Age Group:**
- **Infants (0-2):** Need nap times, feeding facilities, stroller access, baby-changing
- **Toddlers (3-5):** Short attention spans, need playgrounds, early bedtimes, kid menus
- **Children (6-12):** Can handle more activities, need engaging experiences, educational focus
- **Teens (13-17):** Want independence, technology access, adventure activities

**Logistics:**
- Shorter travel days for young children
- Hotels with family rooms or connecting rooms
- Proximity to medical facilities
- Kid-friendly restaurants
- Safe neighborhoods

**Activity Filtering:**
- Age-appropriate attractions
- Avoid adult-only venues
- Include dedicated kid activities
- Balance parent interests with kid needs

Provide specific, actionable recommendations."""


class FamilyNeeds(BaseModel):
    """Analyzed family travel needs."""
    age_group: str = Field(..., description="Primary age group: infant/toddler/child/teen/mixed")
    activity_constraints: list[str] = Field(..., description="Activities to avoid")
    activity_preferences: list[str] = Field(..., description="Recommended activity types")
    hotel_requirements: list[str] = Field(..., description="Hotel must-haves")
    schedule_constraints: list[str] = Field(..., description="Timing considerations")
    dining_needs: list[str] = Field(..., description="Food and restaurant requirements")
    safety_notes: list[str] = Field(..., description="Safety considerations")
    packing_suggestions: list[str] = Field(..., description="Essential items to pack")


def create_family_agent() -> Agent:
    """Create the family analyzer agent."""
    return create_agent(
        system_prompt=SYSTEM_PROMPT,
        temperature=0.3
    )


def analyze_family_needs(
    kid_ages: list[int],
    destination: str,
    duration_days: int
) -> FamilyNeeds:
    """
    Analyze family composition and determine travel constraints.

    Args:
        kid_ages: Ages of children traveling
        destination: Travel destination
        duration_days: Trip length

    Returns:
        FamilyNeeds with constraints and recommendations
    """
    agent = create_family_agent()

    ages_str = ", ".join(str(age) for age in kid_ages)

    prompt = f"""Analyze family travel needs for this trip:

**Children's Ages:** {ages_str}
**Destination:** {destination}
**Duration:** {duration_days} days

Provide specific recommendations for:
1. Activity constraints (what to avoid)
2. Activity preferences (what to include)
3. Hotel requirements
4. Schedule constraints (nap times, early dinners, etc.)
5. Dining needs
6. Safety considerations
7. Packing suggestions"""

    return agent.structured_output(FamilyNeeds, prompt)


def get_family_activity_filter(kid_ages: list[int]) -> str:
    """
    Generate activity filtering instructions based on kid ages.

    Args:
        kid_ages: Ages of children

    Returns:
        Filter instructions for activity planner
    """
    if not kid_ages:
        return ""

    min_age = min(kid_ages)
    max_age = max(kid_ages)

    filters = []

    if min_age <= 2:
        filters.extend([
            "MUST have stroller accessibility",
            "AVOID long walking tours (>1 hour)",
            "INCLUDE parks and open spaces for crawling/walking",
            "PRIORITIZE morning activities (before nap time)",
        ])

    if min_age <= 5:
        filters.extend([
            "AVOID museums with 'no touching' policies",
            "INCLUDE playgrounds and interactive exhibits",
            "LIMIT activities to 2-3 hours max",
            "ENSURE restaurants have high chairs and kids menu",
        ])

    if 6 <= max_age <= 12:
        filters.extend([
            "INCLUDE educational but fun activities",
            "ADD interactive museums and science centers",
            "CONSIDER theme parks if available",
        ])

    if max_age >= 13:
        filters.extend([
            "INCLUDE some adventure activities (age-appropriate)",
            "ALLOW some independence time for teens",
            "CONSIDER technology/gaming attractions",
        ])

    return "\n".join(f"- {f}" for f in filters)


def generate_family_recommendations(context: TravelContext) -> str:
    """
    Generate comprehensive family travel recommendations.

    Args:
        context: Travel context with family info

    Returns:
        Family-specific recommendations as text
    """
    agent = create_family_agent()

    ages_str = ", ".join(str(age) for age in context.kid_ages)

    prompt = f"""Generate family travel recommendations:

**Destination:** {context.destination}
**Children's Ages:** {ages_str}
**Duration:** {context.duration_days} days
**Budget:** {context.budget}
**Interests:** {context.interests}

Provide:
1. **Daily Schedule Template** - Ideal timing for a family day
2. **Must-Have Items** - Essential packing list for kids
3. **Emergency Prep** - Medical, safety considerations
4. **Entertainment Ideas** - For flights, restaurants, waiting times
5. **Budget Tips** - Family discounts, free activities for kids"""

    response = agent(prompt)
    return str(response)


def update_context_with_family_needs(context: TravelContext) -> TravelContext:
    """
    Analyze family needs and update context with recommendations.

    Args:
        context: Travel context to update

    Returns:
        Updated context with family recommendations
    """
    if not context.has_kids or not context.kid_ages:
        return context

    # Get detailed family needs
    needs = analyze_family_needs(
        kid_ages=context.kid_ages,
        destination=context.destination or "general",
        duration_days=context.duration_days
    )

    # Store constraints in context
    context.family_constraints = (
        needs.activity_constraints +
        needs.schedule_constraints +
        needs.safety_notes
    )

    # Generate recommendations text
    context.family_recommendations = generate_family_recommendations(context)

    return context
