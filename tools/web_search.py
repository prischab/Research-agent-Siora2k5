# tools/web_search.py
# Web search tool — lets the agent look up current information.

import os
from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()  # reads the keys from your .env file

client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


def web_search(query: str) -> str:
    """
    Search the web and return short snippets from the top results.
    Example: web_search("population of Japan 2024")
    """
    try:
        response = client.search(query, max_results=3)
        results = response.get("results", [])
        if not results:
            return "No results found."

        formatted = []
        for r in results:
            title = r.get("title", "")
            content = r.get("content", "")
            url = r.get("url", "")

            # Trim each snippet to ~250 characters so it's concise, not a wall of text
            snippet = content[:250].strip()
            if len(content) > 250:
                snippet += "..."

            formatted.append(f"- {title}: {snippet} (Source: {url})")

        return "\n\n".join(formatted)
    except Exception as e:
        return f"Error during search: {e}"


# Quick test
if __name__ == "__main__":
    print(web_search("population of Japan 2024"))