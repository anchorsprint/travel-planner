"""Base agent utilities and shared tools."""

import os
import json
from datetime import datetime
from typing import Optional
from strands import Agent, tool
from strands.models import OpenAIModel
from config import DEFAULT_MODEL, FAST_MODEL, TEMPERATURE_FACTUAL, TEMPERATURE_CREATIVE

# Global citation tracker - stores sources used during current step
_citation_tracker = {
    "searches": [],  # List of {query, timestamp}
    "sources": [],   # List of {title, url, snippet}
}


def reset_citations():
    """Reset citation tracker for a new step."""
    global _citation_tracker
    _citation_tracker = {"searches": [], "sources": []}


def get_citations() -> dict:
    """Get citations from the current step."""
    return _citation_tracker.copy()


def get_step_summary() -> str:
    """Get a formatted summary of what this step searched and found."""
    searches = _citation_tracker.get("searches", [])
    sources = _citation_tracker.get("sources", [])

    if not searches and not sources:
        return ""

    lines = []

    # Show searches made
    if searches:
        lines.append("\n**Searches:**")
        for s in searches[:5]:  # Limit to 5
            lines.append(f"  - \"{s['query']}\"")

    # Show sources found
    if sources:
        lines.append(f"\n**Sources ({len(sources)}):**")
        for src in sources[:5]:  # Limit to 5
            title = src["title"][:50] + "..." if len(src["title"]) > 50 else src["title"]
            lines.append(f"  - [{title}]({src['url']})")
        if len(sources) > 5:
            lines.append(f"  - *+{len(sources) - 5} more*")

    return "\n".join(lines)


def add_citation(title: str, url: str, snippet: str, used_for: str = ""):
    """Add a citation to the tracker."""
    # Avoid duplicates
    for source in _citation_tracker["sources"]:
        if source["url"] == url:
            return
    _citation_tracker["sources"].append({
        "title": title,
        "url": url,
        "snippet": snippet[:200] + "..." if len(snippet) > 200 else snippet
    })


def create_agent(
    system_prompt: str,
    model_id: str = DEFAULT_MODEL,
    temperature: float = TEMPERATURE_FACTUAL,
    tools: list = None
) -> Agent:
    """Create a Strands agent with consistent configuration."""
    return Agent(
        model=OpenAIModel(
            model_id=model_id,
            params={"temperature": temperature}
        ),
        system_prompt=system_prompt,
        tools=tools or []
    )


def _tavily_search(query: str, max_results: int = 5) -> list[dict]:
    """
    Search using Tavily API (designed for AI agents).

    Returns list of {title, url, content, score}
    """
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return []

    try:
        import requests
        response = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": api_key,
                "query": query,
                "max_results": max_results,
                "include_answer": True,
                "search_depth": "basic"
            },
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            results = []
            for r in data.get("results", []):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "content": r.get("content", ""),
                    "score": r.get("score", 0)
                })
            return results
    except Exception as e:
        print(f"Tavily search error: {e}")
    return []


def _brave_search(query: str, max_results: int = 5) -> list[dict]:
    """
    Search using Brave Search API.

    Returns list of {title, url, content}
    """
    api_key = os.getenv("BRAVE_API_KEY")
    if not api_key:
        return []

    try:
        import requests
        response = requests.get(
            "https://api.search.brave.com/res/v1/web/search",
            headers={
                "X-Subscription-Token": api_key,
                "Accept": "application/json"
            },
            params={
                "q": query,
                "count": max_results,
                "text_decorations": False,
                "search_lang": "en"
            },
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            results = []
            for r in data.get("web", {}).get("results", [])[:max_results]:
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "content": r.get("description", ""),
                    "score": 0
                })
            return results
    except Exception as e:
        print(f"Brave search error: {e}")
    return []


def _serper_search(query: str, max_results: int = 5) -> list[dict]:
    """
    Search using Serper API (Google Search API).

    Returns list of {title, url, content}
    """
    api_key = os.getenv("SERPER_API_KEY")
    if not api_key:
        return []

    try:
        import requests
        response = requests.post(
            "https://google.serper.dev/search",
            headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
            json={"q": query, "num": max_results},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            results = []
            for r in data.get("organic", [])[:max_results]:
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("link", ""),
                    "content": r.get("snippet", ""),
                    "score": r.get("position", 0)
                })
            return results
    except Exception as e:
        print(f"Serper search error: {e}")
    return []


@tool
def web_search(query: str) -> str:
    """
    Search the web for travel information. Returns results with sources.

    Args:
        query: Search query for travel-related information

    Returns:
        Search results with citations
    """
    # Track the search query
    _citation_tracker["searches"].append({
        "query": query,
        "timestamp": datetime.now().isoformat()
    })

    # Try Brave first (preferred), then Tavily, then Serper
    results = _brave_search(query)
    search_engine = "Brave"

    if not results:
        results = _tavily_search(query)
        search_engine = "Tavily"

    if not results:
        results = _serper_search(query)
        search_engine = "Serper"

    if not results:
        # Fallback to model knowledge with disclaimer
        return f"""[Search Query: "{query}"]

No live search results available (API keys not configured).
Using model knowledge - information may not be current.

To enable live search, add to .env:
- TAVILY_API_KEY=your_key (recommended for AI agents)
- SERPER_API_KEY=your_key (Google Search alternative)
"""

    # Format results and track citations
    formatted = f'[Search: "{query}" via {search_engine}]\n\n'

    for i, r in enumerate(results, 1):
        # Add to citation tracker
        add_citation(
            title=r["title"],
            url=r["url"],
            snippet=r["content"],
            used_for=query
        )

        # Format for agent
        formatted += f"**Source {i}: {r['title']}**\n"
        formatted += f"URL: {r['url']}\n"
        formatted += f"{r['content']}\n\n"

    formatted += f"---\n[{len(results)} sources found and tracked for citation]\n"

    return formatted


@tool
def get_current_date() -> str:
    """Get the current date for planning purposes."""
    return datetime.now().strftime("%Y-%m-%d")
