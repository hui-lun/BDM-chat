import logging

from langchain.tools import tool
from .web_search import search_and_summarize_advanced

logger = logging.getLogger(__name__)

@tool("fetch_and_analyze_web_html", return_direct=True)
def fetch_and_analyze_web_html(query: str) -> dict:
    """
    Used for web analysis and external search, returns a brief summary.
    """
    logger.info("[Tool Branch] Executing fetch_and_analyze_web_html (Web analysis/search)")
    print(f"[fetch_and_analyze_web_html] input query: {query}")
    if not isinstance(query, str) or not query.strip():
        summary = "Please provide webpage content or keywords to analyze or search."
        print(f"[fetch_and_analyze_web_html] summary (empty): {summary}")
    else:
        try:
            print('*****************************')
            summary = search_and_summarize_advanced(query)
            print('[fetch_and_analyze_web_html] search_and_summarize_advanced output:')
            print(summary)
        except Exception as e:
            summary = f"Error occurred during web analysis: {e}"
            print(f"[fetch_and_analyze_web_html] Exception: {summary}")
    new_state = {
        "agent_query": query,
        "summary": summary,
        "next_node": ""
    }
    # logger.debug("[DEBUG] fetch_and_analyze_web_html - output state: %s", new_state)
    return new_state