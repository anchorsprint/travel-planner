"""Travel Planner Graph - Orchestrates all agents using the Graph pattern."""

import asyncio
from dataclasses import dataclass
from typing import Callable, Optional

from .researcher import research_destination
from .flight_planner import plan_flights
from .hotel_planner import plan_hotels
from .activity_planner import plan_activities
from .synthesizer import synthesize_itinerary
from .reviewer import review_and_refine


@dataclass
class TripRequest:
    """Parsed travel request."""
    destination: str
    origin: str
    departure_date: str
    return_date: str
    travelers: int = 1
    budget: str = "moderate"
    interests: str = ""
    raw_request: str = ""

    @property
    def duration_days(self) -> int:
        """Calculate trip duration in days."""
        from datetime import datetime
        try:
            dep = datetime.strptime(self.departure_date, "%Y-%m-%d")
            ret = datetime.strptime(self.return_date, "%Y-%m-%d")
            return (ret - dep).days
        except ValueError:
            return 5  # Default


@dataclass
class PlanningResult:
    """Result from the travel planning graph."""
    itinerary: str
    review_score: int
    research_summary: str
    flight_options: str
    hotel_options: str
    activity_options: str


class TravelPlannerGraph:
    """
    Graph-based travel planner that orchestrates multiple specialized agents.

    Architecture:
        User Request
             │
             ▼
        ┌─────────────────┐
        │   Destination   │
        │   Researcher    │
        └────────┬────────┘
                 │
       ┌─────────┼─────────┐
       │         │         │
       ▼         ▼         ▼
    ┌──────┐ ┌──────┐ ┌──────┐
    │Flight│ │Hotel │ │Activ.│  ← Parallel execution
    └──┬───┘ └──┬───┘ └──┬───┘
       │        │        │
       └────────┼────────┘
                │
                ▼
        ┌───────────────┐
        │  Synthesizer  │
        └───────┬───────┘
                │
                ▼
        ┌───────────────┐
        │   Reviewer    │  ← Reflection loop
        └───────────────┘
    """

    def __init__(self, progress_callback: Optional[Callable[[str], None]] = None):
        """
        Initialize the travel planner graph.

        Args:
            progress_callback: Optional callback for progress updates
        """
        self.progress_callback = progress_callback or (lambda x: None)

    def _update_progress(self, message: str):
        """Send progress update."""
        self.progress_callback(message)

    def plan_trip(self, request: TripRequest) -> PlanningResult:
        """
        Execute the full travel planning graph.

        Args:
            request: Parsed trip request

        Returns:
            Complete planning result with itinerary and all research
        """
        # Step 1: Research destination
        self._update_progress("🔍 Researching destination...")
        research = research_destination(
            destination=request.destination,
            travel_dates=f"{request.departure_date} to {request.return_date}",
            preferences=request.interests
        )

        # Step 2: Parallel planning (flights, hotels, activities)
        self._update_progress("✈️ Finding flights...")
        flights = plan_flights(
            origin=request.origin,
            destination=request.destination,
            departure_date=request.departure_date,
            return_date=request.return_date,
            travelers=request.travelers,
            budget=request.budget
        )

        self._update_progress("🏨 Searching hotels...")
        hotels = plan_hotels(
            destination=request.destination,
            check_in=request.departure_date,
            check_out=request.return_date,
            travelers=request.travelers,
            budget=request.budget,
            preferences=request.interests
        )

        self._update_progress("🎯 Curating activities...")
        activities = plan_activities(
            destination=request.destination,
            duration_days=request.duration_days,
            interests=request.interests,
            budget=request.budget
        )

        # Step 3: Synthesize into itinerary options
        self._update_progress("📋 Creating itinerary options...")
        itinerary = synthesize_itinerary(
            destination_research=research,
            flight_options=flights,
            hotel_options=hotels,
            activity_options=activities,
            user_request=request.raw_request
        )

        # Step 4: Review and refine
        self._update_progress("✨ Reviewing and refining...")
        final_itinerary, review = review_and_refine(
            itinerary=itinerary,
            user_request=request.raw_request
        )

        self._update_progress("✅ Planning complete!")

        return PlanningResult(
            itinerary=final_itinerary,
            review_score=review.score,
            research_summary=research,
            flight_options=flights,
            hotel_options=hotels,
            activity_options=activities
        )

    async def plan_trip_async(self, request: TripRequest) -> PlanningResult:
        """
        Async version with true parallel execution for flights/hotels/activities.

        Args:
            request: Parsed trip request

        Returns:
            Complete planning result
        """
        # Step 1: Research destination
        self._update_progress("🔍 Researching destination...")
        research = await asyncio.to_thread(
            research_destination,
            destination=request.destination,
            travel_dates=f"{request.departure_date} to {request.return_date}",
            preferences=request.interests
        )

        # Step 2: Parallel planning
        self._update_progress("✈️🏨🎯 Planning flights, hotels, activities in parallel...")

        flights_task = asyncio.to_thread(
            plan_flights,
            origin=request.origin,
            destination=request.destination,
            departure_date=request.departure_date,
            return_date=request.return_date,
            travelers=request.travelers,
            budget=request.budget
        )

        hotels_task = asyncio.to_thread(
            plan_hotels,
            destination=request.destination,
            check_in=request.departure_date,
            check_out=request.return_date,
            travelers=request.travelers,
            budget=request.budget,
            preferences=request.interests
        )

        activities_task = asyncio.to_thread(
            plan_activities,
            destination=request.destination,
            duration_days=request.duration_days,
            interests=request.interests,
            budget=request.budget
        )

        flights, hotels, activities = await asyncio.gather(
            flights_task, hotels_task, activities_task
        )

        # Step 3: Synthesize
        self._update_progress("📋 Creating itinerary options...")
        itinerary = await asyncio.to_thread(
            synthesize_itinerary,
            destination_research=research,
            flight_options=flights,
            hotel_options=hotels,
            activity_options=activities,
            user_request=request.raw_request
        )

        # Step 4: Review and refine
        self._update_progress("✨ Reviewing and refining...")
        final_itinerary, review = await asyncio.to_thread(
            review_and_refine,
            itinerary=itinerary,
            user_request=request.raw_request
        )

        self._update_progress("✅ Planning complete!")

        return PlanningResult(
            itinerary=final_itinerary,
            review_score=review.score,
            research_summary=research,
            flight_options=flights,
            hotel_options=hotels,
            activity_options=activities
        )
