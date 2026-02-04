"""Holiday Planner Agent - Researches holidays and suggests optimal travel dates."""

from strands import Agent
from .base import create_agent, web_search, get_current_date
from .intents import TravelContext

SYSTEM_PROMPT = """You are a holiday and travel date specialist. Your job is to research public holidays, school holidays, and suggest optimal travel dates.

When researching holidays, provide:
1. **Public Holidays** - Official government holidays in the origin country
2. **School Holidays** - School break periods (important for family travel)
3. **Long Weekends** - Holidays that create 3-4 day weekends
4. **Festival Periods** - Cultural celebrations that might affect travel

When suggesting travel dates, consider:
- Align with origin country holidays for easier leave planning
- Check destination for peak/off-peak seasons
- Avoid destination holidays that might mean closures
- Consider weather and crowds

Use web_search to find current holiday calendars.
Always verify dates as they change year to year."""


MALAYSIA_HOLIDAYS_PROMPT = """Research Malaysia public holidays and school holidays for travel planning.

Focus on:
1. Public holidays (federal and state)
2. School holiday periods (March, May-June, August, November-December)
3. Major festivals: CNY, Hari Raya Aidilfitri, Deepavali, Christmas
4. Long weekend opportunities

Use get_current_date to know the current year."""


def create_holiday_agent() -> Agent:
    """Create the holiday planner agent."""
    return create_agent(
        system_prompt=SYSTEM_PROMPT,
        tools=[web_search, get_current_date],
        temperature=0.3
    )


def research_origin_holidays(
    country: str = "Malaysia",
    year: int = None
) -> str:
    """
    Research public holidays and school breaks in the origin country.

    Args:
        country: Origin country (default: Malaysia)
        year: Year to research (default: current year)

    Returns:
        Holiday information for travel planning
    """
    agent = create_holiday_agent()

    year_str = str(year) if year else "2026"

    prompt = f"""Research {country} holidays for {year_str} travel planning:

1. List all public holidays with dates
2. School holiday periods
3. Long weekend opportunities (when holidays fall on Thu/Tue creating 4-day weekends)
4. Major festivals and their typical dates

Use web_search to find the official {country} holiday calendar for {year_str}."""

    response = agent(prompt)
    return str(response)


def research_destination_events(
    destination: str,
    travel_period: str
) -> str:
    """
    Research events and holidays at the destination during travel period.

    Args:
        destination: Travel destination
        travel_period: When the user plans to travel (dates or month)

    Returns:
        Destination events and considerations
    """
    agent = create_holiday_agent()

    prompt = f"""Research events and holidays at {destination} during {travel_period}:

1. Local public holidays (might mean closures)
2. Festivals and events (could enhance or complicate travel)
3. Peak tourist seasons
4. Any travel advisories or considerations

Use web_search to find current information."""

    response = agent(prompt)
    return str(response)


def suggest_travel_dates(
    context: TravelContext,
    destination: str,
    preferred_month: str = None,
    duration_days: int = 5
) -> str:
    """
    Suggest optimal travel dates based on holidays and preferences.

    Args:
        context: Travel context with holiday preferences
        destination: Where user wants to go
        preferred_month: Preferred travel month (optional)
        duration_days: Desired trip length

    Returns:
        Suggested travel date ranges with reasoning
    """
    agent = create_holiday_agent()

    family_note = ""
    if context.has_kids:
        family_note = f"""
**Family Considerations:**
- Traveling with kids ages: {context.kid_ages}
- Prioritize school holiday periods
- Avoid exam periods"""

    month_preference = f"Preferred month: {preferred_month}" if preferred_month else "Flexible on timing"

    prompt = f"""Suggest optimal travel dates for this trip:

**Destination:** {destination}
**Origin Country:** {context.origin_country}
**Trip Duration:** {duration_days} days
**{month_preference}**
{family_note}

Research and suggest 3 optimal travel windows:
1. **Best Option** - Ideal alignment with holidays and destination conditions
2. **Budget Option** - Avoid peak seasons for better prices
3. **Family Option** - Best for school holiday alignment (if applicable)

For each suggestion provide:
- Specific dates (e.g., "March 15-20, 2026")
- Why these dates work well
- Any holidays/events to be aware of
- Expected crowd levels and prices

Use web_search to verify holiday dates and destination seasonality."""

    response = agent(prompt)
    return str(response)


def update_context_with_holidays(context: TravelContext) -> TravelContext:
    """
    Research holidays and update the context with findings.

    Args:
        context: Travel context to update

    Returns:
        Updated context with holiday information
    """
    # Research origin holidays if needed
    if context.check_origin_holidays or context.flexible_dates:
        holiday_info = research_origin_holidays(context.origin_country)
        context.holiday_info = holiday_info

    # Research destination events if we have a destination
    if context.destination and context.departure_date:
        events = research_destination_events(
            context.destination,
            f"{context.departure_date} to {context.return_date}"
        )
        context.holiday_info += f"\n\n## Destination Events\n{events}"

    return context
