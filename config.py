"""Configuration for the Travel Planner."""

import os
from dotenv import load_dotenv

load_dotenv()

# Model settings (OpenAI)
DEFAULT_MODEL = os.getenv("MODEL_ID", "gpt-4o")
FAST_MODEL = os.getenv("FAST_MODEL_ID", "gpt-4o-mini")
QUALITY_MODEL = "gpt-4o"

# Agent settings
MAX_REFLECTION_ITERATIONS = 2
TEMPERATURE_CREATIVE = 0.8
TEMPERATURE_FACTUAL = 0.3
