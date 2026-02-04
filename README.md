# 🌍 Travel Planner

AI-powered travel planning system using **Strands Agents** (Graph Pattern) + **Chainlit** UI.

## Architecture

```
User Request
     │
     ▼
┌─────────────────┐
│     Parser      │  ← Extract structured trip details
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Researcher    │  ← Destination info, best times, tips
└────────┬────────┘
         │
   ┌─────┼─────┐
   │     │     │
   ▼     ▼     ▼
┌─────┐┌─────┐┌─────┐
│Flight││Hotel││Activ│  ← Parallel execution
└──┬──┘└──┬──┘└──┬──┘
   │      │      │
   └──────┼──────┘
          │
          ▼
  ┌───────────────┐
  │  Synthesizer  │  ← Create 2 itinerary options
  └───────┬───────┘
          │
          ▼
  ┌───────────────┐
  │   Reviewer    │  ← Reflection loop for quality
  └───────────────┘
```

## Setup

### 1. Install dependencies

```bash
cd travel-planner
pip install -r requirements.txt
```

### 2. Configure OpenAI API key

Copy `.env.example` to `.env` and add your OpenAI API key:

```bash
cp .env.example .env
```

Edit `.env`:
```
OPENAI_API_KEY=sk-your-api-key-here
```

### 3. Run the app

```bash
chainlit run app.py
```

Open http://localhost:8089 in your browser.

## Usage

Simply describe your trip:

- "Plan a 5-day trip to Tokyo in April, budget $3000"
- "Week in Paris next month, love food and museums"
- "Weekend Barcelona getaway, luxury budget"

The system will:
1. Parse your request
2. Research the destination
3. Find flights, hotels, and activities (in parallel)
4. Create 2 itinerary options
5. Review and refine for quality

## Project Structure

```
travel-planner/
├── app.py                 # Chainlit UI
├── config.py              # Configuration
├── requirements.txt       # Dependencies
├── .env.example           # Environment template
├── chainlit.md            # Welcome message
├── .chainlit/
│   └── config.toml        # Chainlit settings
└── agents/
    ├── __init__.py
    ├── base.py            # Shared utilities & tools
    ├── parser.py          # Request parser agent
    ├── researcher.py      # Destination researcher
    ├── flight_planner.py  # Flight planning
    ├── hotel_planner.py   # Hotel planning
    ├── activity_planner.py# Activity curation
    ├── synthesizer.py     # Itinerary creation
    ├── reviewer.py        # Quality review (reflection)
    └── graph.py           # Main orchestrator
```

## Customization

### Add Web Search

Replace the placeholder in `agents/base.py` with a real search API:

```python
@tool
def web_search(query: str) -> str:
    # Integrate Tavily, SerpAPI, or Brave Search
    import tavily
    client = tavily.Client(api_key=os.getenv("TAVILY_API_KEY"))
    results = client.search(query)
    return results
```

### Change Models

Edit `config.py` to use different Bedrock models:

```python
DEFAULT_MODEL = "anthropic.claude-sonnet-4-20250514-v1:0"  # Higher quality
FAST_MODEL = "amazon.nova-lite-v1:0"      # Faster/cheaper
```

## License

MIT
