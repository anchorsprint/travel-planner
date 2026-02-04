"""Request Parser Agent - Extracts structured trip details from natural language."""

from pydantic import BaseModel, Field
from typing import Optional
from strands import Agent
from .base import create_agent, get_current_date


class ParsedTripRequest(BaseModel):
    """Structured trip request extracted from natural language."""
    destination: str = Field(..., description="Destination city or country")
    origin: str = Field(default="", description="Departure city (if mentioned)")
    departure_date: str = Field(..., description="Start date in YYYY-MM-DD format")
    return_date: str = Field(..., description="End date in YYYY-MM-DD format")
    travelers: int = Field(default=1, description="Number of travelers")
    budget: str = Field(default="moderate", description="Budget level: budget/moderate/luxury")
    interests: str = Field(default="", description="Travel interests and preferences")
    needs_clarification: bool = Field(default=False, description="True if key info is missing")
    clarification_needed: str = Field(default="", description="What info is missing")


SYSTEM_PROMPT = """You are a travel request parser. Extract structured trip details from natural language.

Guidelines:
- Convert relative dates (e.g., "next month", "in 2 weeks") to YYYY-MM-DD format
- If origin city is not mentioned, leave it empty
- Infer budget from context clues (e.g., "cheap" = budget, "splurge" = luxury)
- Extract interests from mentions of activities (e.g., "love food" → "food, culinary")
- If critical info is missing (destination OR dates), set needs_clarification=True

Use the get_current_date tool to resolve relative dates accurately."""


def create_parser_agent() -> Agent:
    """Create the request parser agent."""
    return create_agent(
        system_prompt=SYSTEM_PROMPT,
        tools=[get_current_date],
        temperature=0.1  # Very factual for parsing
    )


def parse_request(user_message: str) -> ParsedTripRequest:
    """
    Parse a natural language trip request into structured data.

    Args:
        user_message: User's travel request in natural language

    Returns:
        Structured trip request
    """
    agent = create_parser_agent()

    prompt = f"""Parse this travel request into structured data:

"{user_message}"

Extract: destination, origin (if mentioned), dates, number of travelers, budget level, and interests.
Use get_current_date to resolve any relative dates like "next week" or "in March"."""

    return agent.structured_output(ParsedTripRequest, prompt)
