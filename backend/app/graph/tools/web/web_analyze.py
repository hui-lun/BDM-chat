import logging

from langchain.tools import tool
from .web_search import search_and_summarize

logger = logging.getLogger(__name__)

@tool("fetch_and_analyze_web_html", return_direct=True)
def fetch_and_analyze_web_html(query: str) -> dict:
    """
    Used for web analysis and external search, returns a brief summary.
    """
    logger.info("[web_analyze] Executing web analysis/search")
    logger.debug(f"[web_analyze] Input query: {query}")
    
    if not isinstance(query, str) or not query.strip():
        summary = "Please provide webpage content or keywords to analyze or search."
        logger.warning("[web_analyze] Empty or invalid query provided")
    else:
        try:
            logger.debug("[web_analyze] Starting web search and summarization")
            # summary = search_and_summarize_advanced(query)
            summary = search_and_summarize(query)
            logger.info("[web_analyze] Successfully completed web search and summarization")
            logger.debug(f"[web_analyze] Generated summary: {summary}")
        except Exception as e:
            error_msg = f"Error occurred during web analysis: {e}"
            logger.error(f"[web_analyze] {error_msg}")
            summary = error_msg

    return {
        "summary": summary,
        "next_node": "beauty_output_web"
    }