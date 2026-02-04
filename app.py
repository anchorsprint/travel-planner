"""Chainlit app for the Smart Travel Planner with real-time progress."""

import sys
import io

# Fix Windows encoding for Unicode characters (emojis, etc.)
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import asyncio
import chainlit as cl
from agents.intents import TravelIntent, TravelContext
from agents.intent_router import detect_intents, build_context_from_intents
from agents.parser import parse_request
from agents.holiday_planner import update_context_with_holidays
from agents.family_analyzer import update_context_with_family_needs, get_family_activity_filter
from agents.quick_answer import answer_travel_question, answer_with_family_focus
from agents.researcher import research_destination
from agents.flight_planner import plan_flights
from agents.hotel_planner import plan_hotels
from agents.activity_planner import plan_activities
from agents.synthesizer import synthesize_itinerary
from agents.reviewer import review_and_refine
from agents.base import reset_citations, get_step_summary


@cl.on_chat_start
async def start():
    """Initialize the chat session."""
    await cl.Message(
        content="""# 🌍 Smart Travel Planner

Welcome! I'm your intelligent travel assistant. I can help with:

**🗺️ Full Trip Planning**
- "Plan a 5-day trip to Tokyo in April"

**👨‍👩‍👧‍👦 Family Travel**
- "Plan a trip to Bali with my kids (ages 3 and 7)"

**📅 Holiday-Aware Planning**
- "When should I visit Japan in 2026 during Malaysian holidays?"
- "Plan a trip during CNY school break with my family"

**❓ Quick Questions**
- "Is April good for visiting Tokyo?"
- "Is Thailand safe for kids?"

What would you like help with?"""
    ).send()


@cl.on_message
async def main(message: cl.Message):
    """Handle user messages with real-time progress updates."""
    user_input = message.content

    # Reset citation tracker for new request
    reset_citations()

    # Step 1: Detect intent
    async with cl.Step(name="🧠 Understanding your request") as intent_step:
        intent_step.output = "Analyzing what you need..."

        try:
            detected = await asyncio.to_thread(detect_intents, user_input)
            context = build_context_from_intents(user_input, detected)
        except Exception as e:
            await cl.Message(content=f"❌ Error detecting intent: {str(e)}").send()
            return

        intents = [i.value for i in context.intents]
        intent_display = ", ".join(intents) if intents else "general inquiry"

        extras = []
        if context.has_kids:
            extras.append(f"👨‍👩‍👧 Family with kids (ages: {', '.join(str(a) for a in context.kid_ages)})")
        if context.needs_holiday_research:
            extras.append(f"📅 Holiday-aware ({context.origin_country})")

        intent_step.output = f"**Detected:** {intent_display}\n" + "\n".join(extras)

    # Quick question - fast path
    if context.is_quick_question:
        async with cl.Step(name="💬 Answering") as step:
            step.output = "Finding answer..."
            if context.has_kids:
                answer = await asyncio.to_thread(answer_with_family_focus, user_input, context.kid_ages)
            else:
                answer = await asyncio.to_thread(answer_travel_question, user_input, context)
            step.output = "✓ Done"

        await cl.Message(content=f"## 💬 Quick Answer\n\n{answer}\n\n---\n*Want me to plan a full trip? Just ask!*").send()
        return

    # Step 2: Parse trip details
    async with cl.Step(name="📋 Extracting trip details") as parse_step:
        parse_step.output = "Parsing your request..."

        try:
            parsed = await asyncio.to_thread(parse_request, user_input)

            context.destination = parsed.destination
            context.origin = parsed.origin or context.origin
            context.departure_date = parsed.departure_date
            context.return_date = parsed.return_date
            context.budget = parsed.budget
            context.interests = parsed.interests
            if not context.has_kids:
                context.travelers = parsed.travelers

            parse_step.output = f"✓ **{context.destination}** | {context.departure_date} to {context.return_date} | {context.travelers} travelers"
        except Exception as e:
            await cl.Message(content=f"❌ Error parsing request: {str(e)}").send()
            return

    # Step 3: Holiday research (if needed)
    if context.needs_holiday_research:
        async with cl.Step(name="📅 Checking holidays") as holiday_step:
            holiday_step.output = f"Researching {context.origin_country} holidays..."
            reset_citations()

            try:
                context = await asyncio.to_thread(update_context_with_holidays, context)
                step_info = get_step_summary()
                holiday_step.output = f"✓ Holiday calendar checked{step_info}"
            except Exception as e:
                holiday_step.output = f"⚠️ Holiday check failed: {str(e)}"

    # Step 4: Family analysis (if needed)
    if context.needs_family_planning:
        async with cl.Step(name="👨‍👩‍👧‍👦 Analyzing family needs") as family_step:
            family_step.output = f"Setting up for kids ages {', '.join(str(a) for a in context.kid_ages)}..."
            reset_citations()

            try:
                context = await asyncio.to_thread(update_context_with_family_needs, context)
                step_info = get_step_summary()
                family_step.output = f"✓ Family filters ready ({context.get_kid_age_group()}-friendly){step_info}"
            except Exception as e:
                family_step.output = f"⚠️ Family analysis failed: {str(e)}"

    # Step 5: Destination research
    async with cl.Step(name="🔍 Researching destination") as research_step:
        research_step.output = f"Learning about {context.destination}..."
        reset_citations()  # Reset for this step

        try:
            preferences = _build_preferences(context)
            research = await asyncio.to_thread(
                research_destination,
                context.destination,
                f"{context.departure_date} to {context.return_date}",
                preferences
            )
            context.destination_research = research
            step_info = get_step_summary()
            research_step.output = f"✓ {context.destination} research complete{step_info}"
        except Exception as e:
            await cl.Message(content=f"❌ Error researching destination: {str(e)}").send()
            return

    # Step 6-8: Parallel planning (flights, hotels, activities)
    # Reset citations for parallel search phase
    reset_citations()

    async with cl.Step(name="✈️ Finding flights") as flights_step:
        flights_step.output = "Searching flights..."

    async with cl.Step(name="🏨 Searching hotels") as hotels_step:
        hotels_step.output = "Finding accommodations..."

    async with cl.Step(name="🎯 Curating activities") as activities_step:
        activities_step.output = "Discovering things to do..."

    try:
        # Run in parallel
        flights_task = asyncio.to_thread(
            plan_flights,
            context.origin or "your city",
            context.destination,
            context.departure_date,
            context.return_date,
            context.travelers,
            context.budget
        )

        hotels_task = asyncio.to_thread(
            plan_hotels,
            context.destination,
            context.departure_date,
            context.return_date,
            context.travelers,
            context.budget,
            _build_hotel_preferences(context)
        )

        family_filter = get_family_activity_filter(context.kid_ages) if context.has_kids else ""
        activities_task = asyncio.to_thread(
            plan_activities,
            context.destination,
            context.duration_days,
            _build_activity_interests(context),
            context.budget,
            family_filter,
            context.kid_ages if context.has_kids else None
        )

        flights, hotels, activities = await asyncio.gather(flights_task, hotels_task, activities_task)

        # Get combined search info for all parallel tasks
        step_info = get_step_summary()
        flights_step.output = f"✓ Flight options found{step_info}"
        hotels_step.output = f"✓ Hotels found"
        activities_step.output = f"✓ Activities curated"

    except Exception as e:
        await cl.Message(content=f"❌ Error planning components: {str(e)}").send()
        return

    # Step 9: Create itinerary
    async with cl.Step(name="📋 Creating itinerary") as synth_step:
        synth_step.output = "Building your perfect trip..."

        try:
            enhanced_request = _build_enhanced_request(context)
            itinerary = await asyncio.to_thread(
                synthesize_itinerary,
                research,
                flights,
                hotels,
                activities,
                enhanced_request
            )
            synth_step.output = "✓ 2 itinerary options created"
        except Exception as e:
            await cl.Message(content=f"❌ Error creating itinerary: {str(e)}").send()
            return

    # Step 10: Quality review
    async with cl.Step(name="✨ Quality review") as review_step:
        review_step.output = "Reviewing and refining..."

        try:
            final_itinerary, review = await asyncio.to_thread(
                review_and_refine,
                itinerary,
                enhanced_request
            )
            review_step.output = f"✓ Quality score: {review.score}/10"
        except Exception as e:
            final_itinerary = itinerary
            review = type('obj', (object,), {'score': 'N/A'})()
            review_step.output = "⚠️ Review skipped"

    # Build final response
    family_badge = ""
    if context.has_kids:
        family_badge = f"\n**👨‍👩‍👧‍👦 Family Trip** - Activities filtered for kids ages {', '.join(str(a) for a in context.kid_ages)}"

    holiday_badge = ""
    if context.needs_holiday_research:
        holiday_badge = f"\n**📅 Holiday-Aware** - Aligned with {context.origin_country} holidays"

    score = review.score if hasattr(review, 'score') else 'N/A'
    stars = "⭐" * min(score, 10) if isinstance(score, int) else ""

    await cl.Message(
        content=f"""# ✅ Your Trip to {context.destination}

**Quality Score:** {stars} ({score}/10)
{family_badge}{holiday_badge}

---

{final_itinerary}

---

💡 **Want to adjust something?** Just tell me:
- "Make it more budget-friendly"
- "Add more kid activities"
- "Show me different hotel options"
- "I prefer option B, finalize it"
"""
    ).send()


def _build_preferences(context: TravelContext) -> str:
    """Build preference string from context."""
    prefs = [context.interests] if context.interests else []
    if context.has_kids:
        prefs.append(f"traveling with kids (ages: {', '.join(str(a) for a in context.kid_ages)})")
        prefs.append("need kid-friendly options")
    if context.check_origin_holidays:
        prefs.append(f"considering {context.origin_country} holidays")
    return "; ".join(prefs)


def _build_hotel_preferences(context: TravelContext) -> str:
    """Build hotel preferences from context."""
    prefs = []
    if context.has_kids:
        prefs.append("family rooms or connecting rooms")
        if context.kid_ages and min(context.kid_ages) <= 5:
            prefs.append("baby crib available")
        prefs.append("safe neighborhood")
        prefs.append("near family attractions")
    return ", ".join(prefs) if prefs else ""


def _build_activity_interests(context: TravelContext) -> str:
    """Build activity interests string with family considerations."""
    interests = [context.interests] if context.interests else []
    if context.has_kids:
        age_group = context.get_kid_age_group()
        interests.append(f"{age_group}-appropriate activities")
        if context.kid_ages and min(context.kid_ages) <= 5:
            interests.append("playgrounds, parks")
        if context.kid_ages and any(6 <= age <= 12 for age in context.kid_ages):
            interests.append("interactive museums, educational fun")
        if context.kid_ages and any(age >= 13 for age in context.kid_ages):
            interests.append("adventure activities for teens")
    return ", ".join(interests)


def _build_enhanced_request(context: TravelContext) -> str:
    """Build enhanced request string with all context."""
    parts = [context.raw_request]
    if context.has_kids:
        parts.append(f"\n\n**Family Info:** Traveling with {len(context.kid_ages)} kids (ages: {', '.join(str(a) for a in context.kid_ages)})")
        if context.family_constraints:
            parts.append(f"Constraints: {'; '.join(context.family_constraints[:5])}")
    if context.holiday_info:
        parts.append(f"\n\n**Holiday Context:**\n{context.holiday_info[:500]}...")
    return "\n".join(parts)


@cl.on_settings_update
async def setup_settings(settings):
    """Handle settings updates."""
    pass
