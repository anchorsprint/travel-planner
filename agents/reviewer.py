"""Quality Reviewer Agent - Reviews and improves travel plans using reflection."""

from pydantic import BaseModel, Field
from strands import Agent
from .base import create_agent
from config import MAX_REFLECTION_ITERATIONS

SYSTEM_PROMPT = """You are a senior travel consultant who reviews and improves travel itineraries.

When reviewing an itinerary, evaluate:
1. **Completeness** - Are all trip components covered?
2. **Practicality** - Is the schedule realistic? Enough time between activities?
3. **Value** - Good balance of cost and experience?
4. **Logistics** - Transport between activities considered?
5. **Balance** - Mix of activities, rest, and meals?

Be constructive and specific in your feedback.
If improvements are needed, explain exactly what to fix."""


class ReviewResult(BaseModel):
    """Result of itinerary review."""
    score: int = Field(..., ge=1, le=10, description="Quality score 1-10")
    is_acceptable: bool = Field(..., description="True if score >= 7")
    strengths: list[str] = Field(..., description="What's good about the itinerary")
    improvements: list[str] = Field(..., description="Specific improvements needed")
    summary: str = Field(..., description="Brief overall assessment")


def create_reviewer_agent() -> Agent:
    """Create the quality reviewer agent."""
    return create_agent(
        system_prompt=SYSTEM_PROMPT,
        temperature=0.3
    )


def review_itinerary(itinerary: str, user_request: str) -> ReviewResult:
    """
    Review an itinerary and provide structured feedback.

    Args:
        itinerary: The itinerary to review
        user_request: Original user request for context

    Returns:
        Structured review with score and feedback
    """
    agent = create_reviewer_agent()

    prompt = f"""Review this travel itinerary:

## Original Request
{user_request}

## Itinerary to Review
{itinerary}

---

Evaluate the itinerary on completeness, practicality, value, logistics, and balance.
Provide a score from 1-10 and specific feedback."""

    return agent.structured_output(ReviewResult, prompt)


def improve_itinerary(itinerary: str, feedback: ReviewResult) -> str:
    """
    Improve an itinerary based on review feedback.

    Args:
        itinerary: The original itinerary
        feedback: Review feedback with improvements needed

    Returns:
        Improved itinerary
    """
    agent = create_agent(
        system_prompt="You are a travel itinerary editor. Improve itineraries based on specific feedback while maintaining their core structure and theme.",
        temperature=0.5
    )

    improvements = "\n".join(f"- {imp}" for imp in feedback.improvements)

    prompt = f"""Improve this itinerary based on the feedback:

## Current Itinerary
{itinerary}

## Feedback (Score: {feedback.score}/10)
{feedback.summary}

## Specific Improvements Needed
{improvements}

---

Revise the itinerary to address these issues. Keep the same format and themes."""

    response = agent(prompt)
    return str(response)


def review_and_refine(itinerary: str, user_request: str) -> tuple[str, ReviewResult]:
    """
    Review and iteratively refine an itinerary.

    Args:
        itinerary: Initial itinerary
        user_request: Original user request

    Returns:
        Tuple of (final itinerary, final review)
    """
    current_itinerary = itinerary

    for iteration in range(MAX_REFLECTION_ITERATIONS):
        review = review_itinerary(current_itinerary, user_request)

        if review.is_acceptable:
            return current_itinerary, review

        # Improve based on feedback
        current_itinerary = improve_itinerary(current_itinerary, review)

    # Final review after all iterations
    final_review = review_itinerary(current_itinerary, user_request)
    return current_itinerary, final_review
