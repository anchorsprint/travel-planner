"""Quick Answer Agent - Provides fast answers to travel inquiries without full planning."""

from strands import Agent
from .base import create_agent, web_search, get_current_date
from .intents import TravelContext

SYSTEM_PROMPT = """You are a quick travel advisor. Your job is to provide fast, helpful answers to travel questions WITHOUT creating full itineraries.

You handle questions like:
- "Is April good for visiting Tokyo?"
- "What's the weather like in Bali in December?"
- "Is it safe to travel to Thailand with kids?"
- "How expensive is Singapore compared to Malaysia?"
- "Do I need a visa for Japan?"

Provide:
1. **Direct Answer** - Answer the question clearly upfront
2. **Key Points** - 3-5 bullet points with relevant details
3. **Quick Tips** - Practical advice related to the question
4. **Follow-up** - Offer to plan a full itinerary if they want

Keep responses concise but helpful. Use web_search for current information."""


def create_quick_answer_agent() -> Agent:
    """Create the quick answer agent."""
    return create_agent(
        system_prompt=SYSTEM_PROMPT,
        tools=[web_search, get_current_date],
        temperature=0.5
    )


def answer_travel_question(
    question: str,
    context: TravelContext = None
) -> str:
    """
    Provide a quick answer to a travel question.

    Args:
        question: The user's travel question
        context: Optional travel context for additional info

    Returns:
        Quick, helpful answer
    """
    agent = create_quick_answer_agent()

    context_info = ""
    if context:
        if context.has_kids:
            context_info += f"\nNote: User is traveling with kids (ages: {context.kid_ages})"
        if context.origin_country:
            context_info += f"\nUser is from: {context.origin_country}"

    prompt = f"""Answer this travel question quickly and helpfully:

"{question}"
{context_info}

Provide:
1. A direct answer to the question
2. 3-5 key points with relevant details
3. 1-2 practical tips
4. Ask if they'd like help planning a full trip

Keep it concise but informative. Use web_search if you need current data."""

    response = agent(prompt)
    return str(response)


def answer_with_family_focus(
    question: str,
    kid_ages: list[int]
) -> str:
    """
    Answer a travel question with family/kids focus.

    Args:
        question: The user's travel question
        kid_ages: Ages of children

    Returns:
        Family-focused answer
    """
    agent = create_quick_answer_agent()

    ages_str = ", ".join(str(age) for age in kid_ages)

    prompt = f"""Answer this travel question from a FAMILY perspective:

Question: "{question}"
Children's Ages: {ages_str}

Focus on:
- Kid-friendliness of the destination/activity
- Safety considerations for children
- Family logistics (strollers, facilities, etc.)
- Age-appropriate recommendations

Provide a helpful, family-focused answer."""

    response = agent(prompt)
    return str(response)
