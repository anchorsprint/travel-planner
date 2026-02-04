"""Travel Intent Detection and Context Management."""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional
from pydantic import BaseModel, Field


class TravelIntent(Enum):
    """Types of travel intents the system can handle."""
    BASIC_TRIP = "basic_trip"              # Standard itinerary planning
    FAMILY_TRIP = "family_trip"            # Trip with children
    HOLIDAY_RESEARCH = "holiday_research"  # When to travel based on holidays
    DATE_SUGGESTION = "date_suggestion"    # Suggest optimal travel dates
    DESTINATION_INQUIRY = "inquiry"        # Quick question, no full plan
    BUDGET_OPTIMIZATION = "budget"         # Focus on cost savings


class DetectedIntents(BaseModel):
    """Result of intent detection."""
    intents: list[str] = Field(..., description="List of detected intent types")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score")
    reasoning: str = Field(..., description="Why these intents were detected")

    # Family indicators
    has_kids: bool = Field(default=False)
    kid_ages: list[int] = Field(default_factory=list)
    family_size: int = Field(default=1)

    # Holiday indicators
    wants_holiday_alignment: bool = Field(default=False)
    origin_country: str = Field(default="Malaysia")
    flexible_dates: bool = Field(default=False)

    # Query type
    is_quick_question: bool = Field(default=False, description="True if just asking a question, not planning")


@dataclass
class TravelContext:
    """Shared context that flows through all agents."""

    # Original request
    raw_request: str = ""

    # Detected intents
    intents: list[TravelIntent] = field(default_factory=list)

    # Basic trip info
    destination: str = ""
    origin: str = ""
    departure_date: str = ""
    return_date: str = ""
    travelers: int = 1
    budget: str = "moderate"
    interests: str = ""

    # Family context
    has_kids: bool = False
    kid_ages: list[int] = field(default_factory=list)
    family_constraints: list[str] = field(default_factory=list)

    # Holiday context
    origin_country: str = "Malaysia"
    check_origin_holidays: bool = False
    check_destination_events: bool = False
    flexible_dates: bool = False
    suggested_date_ranges: list[dict] = field(default_factory=list)

    # Query type
    is_quick_question: bool = False

    # Research results (populated by agents)
    holiday_info: str = ""
    destination_research: str = ""
    family_recommendations: str = ""

    @property
    def duration_days(self) -> int:
        """Calculate trip duration in days."""
        from datetime import datetime
        try:
            dep = datetime.strptime(self.departure_date, "%Y-%m-%d")
            ret = datetime.strptime(self.return_date, "%Y-%m-%d")
            return (ret - dep).days
        except (ValueError, TypeError):
            return 5  # Default

    @property
    def needs_family_planning(self) -> bool:
        """Check if family-specific planning is needed."""
        return TravelIntent.FAMILY_TRIP in self.intents or self.has_kids

    @property
    def needs_holiday_research(self) -> bool:
        """Check if holiday research is needed."""
        return (
            TravelIntent.HOLIDAY_RESEARCH in self.intents or
            TravelIntent.DATE_SUGGESTION in self.intents or
            self.check_origin_holidays or
            self.flexible_dates
        )

    @property
    def needs_full_itinerary(self) -> bool:
        """Check if full itinerary planning is needed."""
        return not self.is_quick_question and TravelIntent.BASIC_TRIP in self.intents

    def get_kid_age_group(self) -> str:
        """Get the youngest kid's age group for activity filtering."""
        if not self.kid_ages:
            return "adult"
        min_age = min(self.kid_ages)
        if min_age <= 2:
            return "infant"
        elif min_age <= 5:
            return "toddler"
        elif min_age <= 12:
            return "child"
        else:
            return "teen"
