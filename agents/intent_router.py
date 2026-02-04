"""Intent Router Agent - Intelligently detects user intent and routes to appropriate agents."""

from strands import Agent
from .base import create_agent
from .intents import TravelIntent, DetectedIntents, TravelContext

SYSTEM_PROMPT = """You are an intelligent travel intent analyzer. Your job is to understand what the user really wants and detect all relevant intents from their message.

Analyze the user's message and detect ALL applicable intents:

1. **BASIC_TRIP** - User wants a full travel itinerary planned
   - Triggers: "plan a trip", "itinerary for", "traveling to"

2. **FAMILY_TRIP** - Trip involves children
   - Triggers: "with kids", "family trip", "my son/daughter", mentions ages, "child-friendly"
   - Extract: kid ages, family size

3. **HOLIDAY_RESEARCH** - User wants to align travel with holidays
   - Triggers: "public holiday", "school holiday", "long weekend", "CNY", "Hari Raya", "Deepavali"
   - Also: "when is good time", "best time considering holidays"

4. **DATE_SUGGESTION** - User wants you to suggest optimal dates
   - Triggers: "when should I", "suggest dates", "best time to visit", flexible on dates
   - Indicates: flexible_dates = True

5. **DESTINATION_INQUIRY** - Quick question, not full planning
   - Triggers: "is X good for", "how is", "what's the weather", "is it safe"
   - These need quick answers, not full itineraries

6. **BUDGET_OPTIMIZATION** - Focus on saving money
   - Triggers: "cheap", "budget", "affordable", "save money"

IMPORTANT:
- Multiple intents can be detected (e.g., FAMILY_TRIP + HOLIDAY_RESEARCH + BASIC_TRIP)
- Extract kid ages if mentioned (e.g., "5-year-old" → [5])
- Detect origin country from context (default: Malaysia)
- Set is_quick_question=True for inquiries that don't need full planning"""


def create_intent_router() -> Agent:
    """Create the intent router agent."""
    return create_agent(
        system_prompt=SYSTEM_PROMPT,
        temperature=0.1  # Very precise for classification
    )


def detect_intents(user_message: str) -> DetectedIntents:
    """
    Analyze user message and detect all relevant travel intents.

    Args:
        user_message: The user's travel-related message

    Returns:
        DetectedIntents with all identified intents and extracted info
    """
    agent = create_intent_router()

    prompt = f"""Analyze this travel request and detect all applicable intents:

"{user_message}"

Detect:
1. All applicable intent types (basic_trip, family_trip, holiday_research, date_suggestion, inquiry, budget)
2. If kids are mentioned, extract their ages
3. If holidays are mentioned, note which ones
4. Determine if this is a quick question or needs full planning
5. Note the origin country if mentioned (default: Malaysia)"""

    return agent.structured_output(DetectedIntents, prompt)


def build_context_from_intents(user_message: str, detected: DetectedIntents) -> TravelContext:
    """
    Build a TravelContext from detected intents.

    Args:
        user_message: Original user message
        detected: Detected intents

    Returns:
        TravelContext populated with intent information
    """
    # Map string intents to enum
    intent_map = {
        "basic_trip": TravelIntent.BASIC_TRIP,
        "family_trip": TravelIntent.FAMILY_TRIP,
        "holiday_research": TravelIntent.HOLIDAY_RESEARCH,
        "date_suggestion": TravelIntent.DATE_SUGGESTION,
        "inquiry": TravelIntent.DESTINATION_INQUIRY,
        "budget": TravelIntent.BUDGET_OPTIMIZATION,
    }

    intents = []
    for intent_str in detected.intents:
        if intent_str.lower() in intent_map:
            intents.append(intent_map[intent_str.lower()])

    # If no specific intent detected, assume basic trip
    if not intents and not detected.is_quick_question:
        intents.append(TravelIntent.BASIC_TRIP)

    return TravelContext(
        raw_request=user_message,
        intents=intents,
        has_kids=detected.has_kids,
        kid_ages=detected.kid_ages,
        travelers=max(detected.family_size, 1 + len(detected.kid_ages)),
        origin_country=detected.origin_country,
        check_origin_holidays=detected.wants_holiday_alignment,
        flexible_dates=detected.flexible_dates,
        is_quick_question=detected.is_quick_question,
    )
