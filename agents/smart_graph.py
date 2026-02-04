"""Smart Travel Planner Graph - Intent-based intelligent routing."""

import asyncio
from typing import Callable, Optional

from .intents import TravelIntent, TravelContext
from .intent_router import detect_intents, build_context_from_intents
from .parser import parse_request
from .holiday_planner import update_context_with_holidays, suggest_travel_dates
from .family_analyzer import update_context_with_family_needs, get_family_activity_filter
from .quick_answer import answer_travel_question, answer_with_family_focus
from .researcher import research_destination
from .flight_planner import plan_flights
from .hotel_planner import plan_hotels
from .activity_planner import plan_activities
from .synthesizer import synthesize_itinerary
from .reviewer import review_and_refine


class SmartTravelPlanner:
    """
    Intent-based travel planner that intelligently routes to appropriate agents.

    Routes based on detected intents:
    - BASIC_TRIP → Full planning pipeline
    - FAMILY_TRIP → Family analyzer + kid-aware planning
    - HOLIDAY_RESEARCH → Holiday planner + date suggestions
    - DESTINATION_INQUIRY → Quick answer agent
    """

    def __init__(self, progress_callback: Optional[Callable[[str, str], None]] = None):
        """
        Initialize the smart travel planner.

        Args:
            progress_callback: Callback for progress updates (step_name, message)
        """
        self.progress_callback = progress_callback or (lambda s, m: None)

    def _update_progress(self, step: str, message: str):
        """Send progress update."""
        self.progress_callback(step, message)

    def process_request(self, user_message: str) -> dict:
        """
        Process a user request with intelligent routing.

        Args:
            user_message: User's travel request

        Returns:
            Dict with response and metadata
        """
        # Step 1: Detect intents
        self._update_progress("intent", "🧠 Understanding your request...")
        detected = detect_intents(user_message)
        context = build_context_from_intents(user_message, detected)

        # Log detected intents
        intent_names = [i.value for i in context.intents]
        self._update_progress("intent", f"Detected: {', '.join(intent_names)}")

        # Step 2: Parse trip details if needed
        if context.needs_full_itinerary or context.needs_holiday_research:
            self._update_progress("parse", "📋 Extracting trip details...")
            parsed = parse_request(user_message)

            # Merge parsed details into context
            context.destination = parsed.destination
            context.origin = parsed.origin or context.origin
            context.departure_date = parsed.departure_date
            context.return_date = parsed.return_date
            context.budget = parsed.budget
            context.interests = parsed.interests

            # Override travelers count if we have family info
            if not context.has_kids:
                context.travelers = parsed.travelers

        # Step 3: Route based on intents
        return self._route_by_intent(context)

    def _route_by_intent(self, context: TravelContext) -> dict:
        """Route to appropriate agents based on detected intents."""

        # Quick question - fast path
        if context.is_quick_question:
            return self._handle_quick_question(context)

        # Date suggestion without destination
        if TravelIntent.DATE_SUGGESTION in context.intents and not context.destination:
            return self._handle_date_suggestion(context)

        # Full planning path
        return self._handle_full_planning(context)

    def _handle_quick_question(self, context: TravelContext) -> dict:
        """Handle quick travel questions."""
        self._update_progress("quick", "💬 Answering your question...")

        if context.has_kids:
            answer = answer_with_family_focus(
                context.raw_request,
                context.kid_ages
            )
        else:
            answer = answer_travel_question(context.raw_request, context)

        return {
            "type": "quick_answer",
            "response": answer,
            "context": context,
        }

    def _handle_date_suggestion(self, context: TravelContext) -> dict:
        """Handle requests for travel date suggestions."""
        self._update_progress("holiday", "📅 Researching holidays and best dates...")

        # Research holidays
        context = update_context_with_holidays(context)

        # Suggest dates
        suggestions = suggest_travel_dates(
            context=context,
            destination=context.destination or "general travel",
            duration_days=context.duration_days or 5
        )

        return {
            "type": "date_suggestion",
            "response": suggestions,
            "holiday_info": context.holiday_info,
            "context": context,
        }

    def _handle_full_planning(self, context: TravelContext) -> dict:
        """Handle full itinerary planning with all relevant agents."""

        # Phase 1: Context enrichment (parallel where possible)
        self._update_progress("enrich", "🔍 Gathering information...")

        # Holiday research if needed
        if context.needs_holiday_research:
            self._update_progress("holiday", "📅 Checking holidays...")
            context = update_context_with_holidays(context)

        # Family analysis if needed
        if context.needs_family_planning:
            self._update_progress("family", "👨‍👩‍👧‍👦 Analyzing family needs...")
            context = update_context_with_family_needs(context)

        # Phase 2: Destination research
        self._update_progress("research", "🔍 Researching destination...")
        research = research_destination(
            destination=context.destination,
            travel_dates=f"{context.departure_date} to {context.return_date}",
            preferences=self._build_preferences(context)
        )
        context.destination_research = research

        # Phase 3: Component planning
        self._update_progress("flights", "✈️ Finding flights...")
        flights = plan_flights(
            origin=context.origin or "your city",
            destination=context.destination,
            departure_date=context.departure_date,
            return_date=context.return_date,
            travelers=context.travelers,
            budget=context.budget
        )

        self._update_progress("hotels", "🏨 Searching hotels...")
        hotel_preferences = self._build_hotel_preferences(context)
        hotels = plan_hotels(
            destination=context.destination,
            check_in=context.departure_date,
            check_out=context.return_date,
            travelers=context.travelers,
            budget=context.budget,
            preferences=hotel_preferences
        )

        self._update_progress("activities", "🎯 Curating activities...")
        activity_filter = get_family_activity_filter(context.kid_ages) if context.has_kids else ""
        activities = plan_activities(
            destination=context.destination,
            duration_days=context.duration_days,
            interests=self._build_activity_interests(context),
            budget=context.budget
        )

        # Phase 4: Synthesis
        self._update_progress("synthesize", "📋 Creating itinerary options...")

        # Build enhanced user request with context
        enhanced_request = self._build_enhanced_request(context)

        itinerary = synthesize_itinerary(
            destination_research=research,
            flight_options=flights,
            hotel_options=hotels,
            activity_options=activities,
            user_request=enhanced_request
        )

        # Phase 5: Review
        self._update_progress("review", "✨ Reviewing and refining...")
        final_itinerary, review = review_and_refine(
            itinerary=itinerary,
            user_request=enhanced_request
        )

        self._update_progress("complete", "✅ Planning complete!")

        return {
            "type": "full_itinerary",
            "response": final_itinerary,
            "review_score": review.score,
            "context": context,
            "components": {
                "research": research,
                "flights": flights,
                "hotels": hotels,
                "activities": activities,
            }
        }

    def _build_preferences(self, context: TravelContext) -> str:
        """Build preference string from context."""
        prefs = [context.interests] if context.interests else []

        if context.has_kids:
            prefs.append(f"traveling with kids (ages: {', '.join(str(a) for a in context.kid_ages)})")
            prefs.append("need kid-friendly options")

        if context.check_origin_holidays:
            prefs.append(f"considering {context.origin_country} holidays")

        return "; ".join(prefs)

    def _build_hotel_preferences(self, context: TravelContext) -> str:
        """Build hotel preferences from context."""
        prefs = []

        if context.has_kids:
            prefs.append("family rooms or connecting rooms")
            if min(context.kid_ages) <= 5:
                prefs.append("baby crib available")
            prefs.append("safe neighborhood")
            prefs.append("near family attractions")

        return ", ".join(prefs) if prefs else ""

    def _build_activity_interests(self, context: TravelContext) -> str:
        """Build activity interests string with family considerations."""
        interests = [context.interests] if context.interests else []

        if context.has_kids:
            age_group = context.get_kid_age_group()
            interests.append(f"{age_group}-appropriate activities")

            if min(context.kid_ages) <= 5:
                interests.append("playgrounds, parks")
            if any(6 <= age <= 12 for age in context.kid_ages):
                interests.append("interactive museums, educational fun")
            if any(age >= 13 for age in context.kid_ages):
                interests.append("adventure activities for teens")

        return ", ".join(interests)

    def _build_enhanced_request(self, context: TravelContext) -> str:
        """Build enhanced request string with all context."""
        parts = [context.raw_request]

        if context.has_kids:
            parts.append(f"\n\n**Family Info:** Traveling with {len(context.kid_ages)} kids (ages: {', '.join(str(a) for a in context.kid_ages)})")
            if context.family_constraints:
                parts.append(f"Constraints: {'; '.join(context.family_constraints[:5])}")

        if context.holiday_info:
            parts.append(f"\n\n**Holiday Context:**\n{context.holiday_info[:500]}...")

        return "\n".join(parts)

    async def process_request_async(self, user_message: str) -> dict:
        """Async version of process_request."""
        # For now, wrap sync version - can be optimized later
        return await asyncio.to_thread(self.process_request, user_message)
